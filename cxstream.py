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
        self.file = None
    
    def is_audio(self):
        return self.type == StreamType.AUDIO
    
    def is_video(self):
        return self.type == StreamType.VIDEO

    def is_subtitle(self):
        return self.type == StreamType.SUBTITLE


class Streams:
    def __init__(self):
        self.streams = []
        self.langs = {}

    def add(self, stream):
        duplicate = False
        for s in self.streams:
            if s.id == stream.id or stream.is_video() and s.is_video():
                duplicate = True
        if not duplicate:
            self.__handle_multi_streams_for_same_language(stream)
            self.streams.append(stream)

    def reset(self):
        self.streams.clear()
    
    def get_ffmpeg_mapping(self):
        if not self.streams:
            # map all streams by default
            return " -map 0"
        mapping = ""
        audio_stream_id = 0
        for s in self.streams:
            if s.enabled and s.type != StreamType.SUBTITLE:
                # subtitles aren't mapped into the output, they are extracted separately
                mapping += " -map " + s.id
                if s.is_audio() and s.lang:
                    mapping += ' -metadata:s:a:{} language={} -metadata:s:a:{} title={}'.format(
                            audio_stream_id, s.lang, audio_stream_id, s.lang)
                    audio_stream_id += 1
        return mapping

    def has_subtitle(self):
        for s in self.streams:
            if s.enabled and s.is_subtitle():
                return True
        return False

    def __handle_multi_streams_for_same_language(self, stream):
        if stream.type in self.langs:
            if stream.lang in self.langs[stream.type]:
                self.langs[stream.type][stream.lang] += 1
            else:
                self.langs[stream.type][stream.lang] = 1
        else:
            self.langs[stream.type] = { stream.lang: 1}
        if self.langs[stream.type][stream.lang] != 1:
            orig_lang = stream.lang
            stream.lang = "{}.{}".format(orig_lang, self.langs[stream.type][orig_lang])
