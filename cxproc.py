#!/usr/bin/python3
# -*- coding: utf-8 -*-
import subprocess

###############################################################################

def terminate(process, unset=False):
    """ Terminate a sub-process """
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
        if unset:
            process = None

###############################################################################

def create_video_parser(input_file):
    """ Create a video parser sub-process """
    return subprocess.Popen(["ffmpeg"
        # input file options:
        # input file:
        , "-i", input_file
        # output file options:
        ,"-map","0:v","-c","copy","-f","null","-y"
        # output file:
        ,"/dev/null"]
        , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        , universal_newlines=True)

###############################################################################

def create_converter(input_file, streams, output_file):
    """ Create converter sub-process """
    converter_command = ("ffmpeg"
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
            " {}").format(input_file, streams.get_ffmpeg_mapping(), output_file)
    print("The converter command: '{}'".format(converter_command))

    return subprocess.Popen(converter_command.split()
        , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        , universal_newlines=True)

