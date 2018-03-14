#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("/lib/convert-x")

from abc import ABC
from cxstream import Stream, Streams
import re
import subprocess
import threading as th
import time

###############################################################################

class AbstractCommand(ABC):
    def __init__(self, command):
        print("Command: '{}'".format(command))
        self.process = subprocess.Popen(command.split()
                , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                , universal_newlines=True)
        self.progress_thread = th.Thread(target=self.__read_next_line)
        self.cancelled = False
    
    def prestart(self):
        """ Override to act right before starting the command
        Return false to cancel start
        """
        return True

    def start(self):
        if self.prestart():
            self.start = time.time()
            self.progress_thread.start()

    def progress(self, line, elapsed_seconds):
        """ Override to process the next line on the command's combined
        stdout & stderr
        Return false to break the progress loop
        """
        return True
    
    def stop(self):
        self.cancelled = True
        self.__terminate()

    def finish(self):
        """ Override to act upon finished processing
        You might want to specify behaviour based on the value of self.cancelled
        """
        pass

    def __terminate(self):
        """ Terminate the command """
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def __read_next_line(self):
        for raw_line in iter(self.process.stdout.readline, ""):
            elapsed = time.time() - self.start
            if self.cancelled or not self.progress(raw_line.rstrip(), elapsed):
                break
        self.process = None
        self.finish()

class VideoParserCommand(AbstractCommand):
    def __init__(self, input_file, finished_cb):
        if input_file is None:
            raise RuntimeError("INTERNAL ERROR: input file cannot be None"
                    " at this stage!")
        super().__init__(("ffmpeg"
            # input file options:
            # input file:
            " -i {}"
            # output file options:
            " -map 0:v -c copy -f null -y"
            # output file:
            " /dev/null").format(input_file))
        self.__finished_cb = finished_cb
        self.__last_match = None
        self.num_of_frames = None
        self.one_percent = None
        self.streams = Streams()
        self.permission_error = False
        self.finished = False
    
    def progress(self, line, elapsed_seconds):
        if re.search("Permission denied", line):
            self.permission_error = True
            return False
        
        match = re.search("^\s*Stream #(\d+:\d+)\(([^:]+)\):\s*([^:]+)", line)
        if match:
            print("'{}''{}''{}'".format(match.group(1), match.group(2)
                , match.group(3)))
            self.streams.add(Stream(stream_id=match.group(1)
                , lang=match.group(2), stream_type=match.group(3)))
        
        match = re.search("^\s*frame=\s*(\d+)", line)
        if match:
            self.__last_match = match
        return True
    
    def finish(self):
        if not self.cancelled:
            self.finished = True
            if self.__last_match:
                self.num_of_frames = int(self.__last_match.group(1))
                self.one_percent = self.num_of_frames / 100
            if self.__finished_cb is not None:
                self.__finished_cb()

class ConverterCommand(AbstractCommand):
    """ Converter command """
    def __init__(self, input_file, streams, output_file
            , num_of_frames, one_percent
            , step_cb, elapsed_cb, left_cb, finished_cb):
        super().__init__(("ffmpeg"
            # input file options:
            # input file:
            " -i {}"
            # output file options:
            " -c copy"
            " -c:s srt"
            " -c:v libxvid -q:v 0"
            " -c:a libmp3lame -q:a 0 -b:a 128k -ac 2"
            "{}"
            " -y"
            # output file:
            " {}").format(input_file, streams.get_ffmpeg_mapping(), output_file))
        self.__percent = 0.0
        self.__progress = 0.0
        self.__frame = 0
        self.__num_of_frames = num_of_frames
        self.__one_percent = one_percent
        self.__step_cb = step_cb
        self.__elapsed_cb = elapsed_cb
        self.__left_cb = left_cb
        self.__finished_cb = finished_cb

    def progress(self, line, elapsed_seconds):
        """ Monitor the progress of the conversion and report it """
        if self.__num_of_frames is not None and self.__one_percent is not None\
                and self.__step_cb is not None and self.__elapsed_cb is not None\
                and self.__left_cb is not None:
            match = re.search("frame=\s*(\d+)", line)
            if match:
                self.__frame = int(match.group(1))
                if self.__frame >= percent:
                    self.__percent = (self.__frame / self.__one_percent)
                    incr = self.__percent - self.__progress
                    self.__step_cb(incr)
                    self.__progress += incr
                    self.__percent = self.__frame + self.__one_percent

            self.__elapsed_cb(elapsed_seconds)
            
            if self.__frame:
                needed_per_frame = elapsed_seconds / self.__frame
                left = self.__num_of_frames - self.__frame
                estimate = left * needed_per_frame
                self.__left_cb(estimate)
        return True

    def finish(self):
        if not self.cancelled and self.__finished_cb is not None:
            self.__finished_cb()
