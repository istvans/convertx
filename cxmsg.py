#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("/lib/convert-x")

from cxutils import AutoNumber

###############################################################################

class Type(AutoNumber):
    START = ()
    STOP = ()
    STOP_ACK = ()
    CLOSE = ()
    CLOSE_ACK = ()
    STEP = ()
    ELAPSED = ()
    LEFT = ()
    DELETE = ()
    SET_CFG = ()
    INPUT_FILE = ()
    OPENED = ()
    OUTPUT_FILE = ()
    FAILED = ()
    FINISHED = ()
    EXTRACTING_SUBTITLES = ()
    UPDATE_CHECK = ()
    UPDATE_AVAIL = ()
    UPDATE_START = ()
    UPDATE_FINISHED = ()
    WARN_UNKNOWN_REMAINING_TIME = ()
    WARN_PERMISSION_ERROR = ()

class Msg:
    def __init__(self, msg_type, *data):
        self.type = msg_type
        self.data = data

