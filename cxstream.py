#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("/lib/convert-x")

from cxutils import AutoNumber

###############################################################################

class StreamType(AutoNumber):
    AUDIO = ()
    SUBTITLE = ()
    VIDEO = ()

class Stream:
    def __init__(self, stream_id, lang, stream_type):
        # TODO The id must be in ffmpeg format! :(
        self.id = stream_id
        self.lang = lang
        if stream_type == "Video":
            self.type = StreamType.VIDEO
        elif stream_type == "Audio":
            self.type = StreamType.AUDIO
        elif stream_type == "Subtitle":
            self.type = StreamType.SUBTITLE
        else:
            raise RuntimeError("Unknown stream type: '{}'".format(stream_type))
        self.enabled = True

class Streams:
    def __init__(self):
        self.streams = []

    def add(self, stream):
        duplicate = False
        for s in self.streams:
            if s.id == stream.id:
                duplicate = True
        if not duplicate:
            self.streams.append(stream)

    def reset(self):
        self.streams.clear()

    def get_ffmpeg_mapping(self):
        if not self.streams:
            # map all streams by default
            return " -map 0"
        mapping = ""
        for s in self.streams:
            if s.enabled:
                mapping += " -map " + s.id
        return mapping

