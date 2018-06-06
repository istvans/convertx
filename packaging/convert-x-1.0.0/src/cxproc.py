# -*- coding: utf-8 -*-
from abc import ABC
import cxpack
from cxstream import Stream, Streams
import pexpect as pe
import re
import shlex
import subprocess
import threading as th
import time

###############################################################################

class AbstractReadOnlyLongCommand(ABC):
    
    ### Public Methods ###

    def __init__(self, command):
        """ Initialise but do not start the command yet """
        self.__command = command
        self.__start_time = None
        self._process = None
        self._progress_thread = th.Thread(target=self.__read_next_line)
        self._cancelled = False
        self._last_line = None

    def start(self):
        """ Start the command and its monitoring in the progress thead """
        if self._prestart():
            self.__start_time = time.time()
            split_command = shlex.split(self.__command)
            self._process = subprocess.Popen(split_command
                    , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                    , universal_newlines=True)
            self._progress_thread.start()
    
    def stop(self):
        self._cancelled = True
        self.__terminate()

    ### Protected Methods ###

    def _prestart(self):
        """ Override to act right before starting the command
        Return false to cancel start
        """
        return True

    def _progress(self, line, elapsed_seconds):
        """ Override to process the next line on the command's combined
        stdout & stderr
        Return false to break the progress loop
        """
        return True

    def _finish(self):
        """ Override to act upon finished processing
        You might want to specify behaviour based on the value of self._cancelled
        self._last_line stores the command's last output line
        """
        pass

    ### Private Methods ###

    def __terminate(self):
        """ Terminate the command """
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def __read_next_line(self):
        for raw_line in iter(self._process.stdout.readline, ""):
            elapsed = time.time() - self.__start_time
            self._last_line = raw_line.rstrip()
            if self._cancelled:
                break
            if not self._progress(self._last_line, elapsed):
                self.__terminate()
                break
        self._process = None
        self._finish()

class VideoParserCommand(AbstractReadOnlyLongCommand):
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
    
    def _progress(self, line, elapsed_seconds):
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
    
    def _finish(self):
        if not self._cancelled:
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

class SubtitleExtractorCommand(AbstractReadOnlyLongCommand):
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
    
    def _finish(self):
        if self.__finished_cb is not None:
            failed = True if self._last_line is None or\
                    not re.search("^\s*video:", self._last_line) else False
            self.__finished_cb(self.__subtitle, failed, self._last_line)

class ConverterCommand(AbstractReadOnlyLongCommand):
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

    def _progress(self, line, elapsed_seconds):
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

    def _finish(self):
        if self.__finished_cb is not None:
            failed = True if self._last_line is None or\
                    not re.search("^\s*video:", self._last_line) else False
            self.__finished_cb(self._cancelled, failed, self._last_line)

###############################################################################
###############################################################################

class ReadWriteShortCommand:
    def __init__(self, command, events=None, timeout=None):
        self.command = command
        self.events = events
        self.timeout = timeout

    def run(self):
        return pe.run(self.command, events=self.events, timeout=self.timeout)

class AbstractReadWriteShortCommand(ABC):
    def __init__(self, command, events=None, timeout=None):
        """ Initialise but do not start the command yet """
        self._command = ReadWriteShortCommand(command, events=events, timeout=timeout)

    def run(self):
        return self._command.run().decode("utf-8")

    def _gen_password_events(self, password):
        password_answer = "{}\n".format(password.get())
        return {"[pP]assword.*:":password_answer, "[jJ]elsz.*:":password_answer}

class UpdateDownloader(AbstractReadWriteShortCommand):
    def __init__(self, password):
        super().__init__(command="sudo apt-get update"
            , events=self._gen_password_events(password))

class UpdateVersionChecker(AbstractReadWriteShortCommand):
    def __init__(self, password):
        super().__init__(command="sudo apt-cache policy {}".format(cxpack.package)
            , events=self._gen_password_events(password))

class UpdateInstaller(AbstractReadWriteShortCommand):
    def __init__(self, password):
        expected_events = self._gen_password_events(password)
        expected_events["Folytatni akarja?"] = "i\n"
        expected_events["Do you want to continue?"] = "y\n"
        super().__init__(command="sudo apt-get install {}".format(cxpack.package)
            , events=expected_events)

################################################################################

class UpdateSearch:
    def __init__(self, password, finished_cb):
        self.__finished_cb = finished_cb
        self.__download = UpdateDownloader(password)
        self.__check = UpdateVersionChecker(password)
        self.__run_thread = th.Thread(target=self._process)
        self.__installed_version = None
        self.__candidate_version = None

    def start(self):
        self.__run_thread.start()

    def _process(self):
        self.__download.run()
        self.__versions_text = self.__check.run()
        installed = re.search("(Installed|Telepítve):\s*(\S+)", self.__versions_text)
        candidate = re.search("(Candidate|Jelölt):\s*(\S+)", self.__versions_text)
        if installed and candidate:
            self.__installed_version = installed.group(1)
            self.__candidate_version = candidate.group(1)
        self._finish()

    def _finish(self):
        if self.__finished_cb is not None:
            failed = True if self.__versions_text is None or self.__installed_version is None or\
                    self.__candidate_version is None else False

            last_line = None
            if self.__versions_text is not None:
                last_line = self.__versions_text.splitlines()[-1]

            self.__finished_cb(failed, self.__installed_version, self.__candidate_version, last_line)

################################################################################

class UpdateInstall:
    def __init__(self, password, finished_cb):
        self.__finished_cb = finished_cb
        self.__install = UpdateInstaller(password)
        self.__check = UpdateVersionChecker(password)
        self.__run_thread = th.Thread(target=self._process)
        self.__installed_version = None
        self.__candidate_version = None
        self.__result = None

    def start(self):
        self.__run_thread.start()

    def _process(self):
        self.__result = self.__install.run()
        versions_text = self.__check.run()
        installed = re.search("(Installed|Telepítve):\s*(\S+)", versions_text)
        candidate = re.search("(Candidate|Jelölt):\s*(\S+)", versions_text)
        if installed and candidate:
            self.__installed_version = installed.group(1)
            self.__candidate_version = candidate.group(1)
        self._finish()

    def _finish(self):
        if self.__finished_cb is not None:
            failed = True if self.__result is None or self.__installed_version is None or\
                self.__candidate_version is None or\
                self.__installed_version != self.__candidate_version else False

            last_line = None
            if self.__result is not None:
                last_line = self.__result.splitlines()[-1]

            self.__finished_cb(failed, self.__installed_version, last_line)
