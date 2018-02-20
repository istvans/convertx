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

def create_mapping(streams):
    mapping = []
    for stream in streams:
        mapping.extend(["-map", "0:{}".format(stream)])
    return mapping

###############################################################################

def create_converter(input_file, optional_streams, output_file):
    """ Create converter sub-process """
    return subprocess.Popen(["ffmpeg"
        # input file options:
        # input file:
        , "-i", input_file
        # output file options:
        , "-map", "0:v", "-vcodec", "libxvid", "-q:v", "0"
        , "-acodec", "libmp3lame", "-q:a", "0", "-b:a", "128k", "-ac", "2"] +
        create_mapping(optional_streams) +
        ["-y"
        # output file:
        , output_file]
        , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        , universal_newlines=True)

