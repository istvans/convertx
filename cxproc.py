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
        """ Initialise but do not start the command yet """
        self.__command = command
        self.__start_time = None
        print("Command: '{}'".format(self.__command))
        self.process = None
        self.progress_thread = th.Thread(target=self.__read_next_line)
        self.cancelled = False
        self.last_line = None
    
    def prestart(self):
        """ Override to act right before starting the command
        Return false to cancel start
        """
        return True

    def start(self):
        """ Start the command and its monitoring in the progress thead """
        if self.prestart():
            self.__start_time = time.time()
            self.process = subprocess.Popen(self.__command.split()
                    , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                    , universal_newlines=True)
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
        self.last_line stores the command's last output line
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
            elapsed = time.time() - self.__start_time
            self.last_line = raw_line.rstrip()
            print(self.last_line)
            if self.cancelled:
                break
            if not self.progress(self.last_line, elapsed):
                self.__terminate()
                break
        self.process = None
        self.finish()

class VideoParserCommand(AbstractCommand):
    def __init__(self, input_file, finished_cb):
        if input_file is None:
            raise RuntimeError("INTERNAL ERROR: input file cannot be None at this stage!")
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
        
        match = re.search("^\s*frame=\s*(\d+)", line)
        if match:
            self.__last_match = match
            return True
        
        stream_id = None
        lang = ""
        stream_type = None
        match = re.search("^\s*Stream #(\d+:\d+)\(([^:]+)\):\s*([^:]+)", line)
        if match:
            stream_id = match.group(1)
            lang = match.group(2)
            stream_type = match.group(3)
        else:
            match = re.search("^\s*Stream #(\d+:\d+):\s*([^:]+)", line)
            if match:
                stream_id = match.group(1)
                stream_type = match.group(2)

        if stream_id is not None and stream_type is not None:
            self.streams.add(Stream(stream_id=stream_id, lang=lang, stream_type=stream_type))
        
        return True
    
    def finish(self):
        if not self.cancelled:
            self.finished = True
            if self.__last_match:
                self.num_of_frames = int(self.__last_match.group(1))
                self.one_percent = self.num_of_frames / 100
            if self.__finished_cb is not None:
                self.__finished_cb()

class Subtitle:
    def __init__(self, str_id, str_file, stream):
        self.id = str_id
        self.file = str_file
        self.stream = stream
        self.extracted = False

class SubtitleExtractorCommand(AbstractCommand):
    def __init__(self, input_file, subtitle, finished_cb):
        super().__init__(("ffmpeg"
            # input file options:
            # input file:
            " -i {}"
            # output file options:
            " -map {}"
            " -y"
            # output file:
            " {}").format(input_file, subtitle.stream.id, subtitle.file))
        self.__subtitle = subtitle
        self.__finished_cb = finished_cb
    
    def finish(self):
        if self.__finished_cb is not None:
            self.failed = True if self.last_line is None or\
                    not re.search("^\s*video:", self.last_line) else False
            self.__finished_cb(self.__subtitle, self.failed, self.last_line)

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
            " -c:v libxvid -q:v 0"
            " -c:a libmp3lame -q:a 0 -b:a 128k -ac 2"
            "{}"
            " -y"
            # output file:
            " {}").format(input_file, streams.get_ffmpeg_mapping(), output_file))
        self.__input_file = input_file
        self.__output_file = output_file
        self.__percent = 0.0
        self.__progress = 0.0
        self.__frame = 0
        self.__num_of_frames = num_of_frames
        self.__one_percent = one_percent
        self.__step_cb = step_cb
        self.__elapsed_cb = elapsed_cb
        self.__left_cb = left_cb
        self.__finished_cb = finished_cb
        self.failed = False

    def progress(self, line, elapsed_seconds):
        """ Monitor the progress of the conversion and report it """
        if self.__num_of_frames is not None and self.__one_percent is not None\
                and self.__step_cb is not None and self.__elapsed_cb is not None\
                and self.__left_cb is not None:
            match = re.search("frame=\s*(\d+)", line)
            if match:
                self.__frame = int(match.group(1))
                if self.__frame >= self.__percent:
                    self.__percent = (self.__frame / self.__one_percent)
                    incr = self.__percent - self.__progress
                    self.__step_cb(incr)
                    self.__progress += incr
                    self.__percent = self.__frame + self.__one_percent

            self.__elapsed_cb(elapsed_seconds)
            
            if self.__frame:
                needed_per_frame = elapsed_seconds / self.__frame
                left_frames = self.__num_of_frames - self.__frame
                estimated_left_time = left_frames * needed_per_frame
                self.__left_cb(estimated_left_time)
        return True

    def finish(self):
        if self.__finished_cb is not None:
            self.failed = True if self.last_line is None or\
                    not re.search("^\s*video:", self.last_line) else False
            self.__finished_cb(self.cancelled, self.failed, self.last_line)
