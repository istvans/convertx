# -*- coding: utf-8 -*-
from cxutils import AutoNumber
###############################################################################

class Type(AutoNumber):
    CLOSE_ACK = ()
    CLOSE = ()
    DELETE = ()
    ELAPSED = ()
    EXTRACTING_SUBTITLES = ()
    FAILED = ()
    FINISHED = ()
    INPUT_FILE = ()
    LEFT = ()
    OPENED = ()
    OUTPUT_FILE = ()
    SET_CFG = ()
    START = ()
    STEP = ()
    STOP_ACK = ()
    STOP = ()
    UPDATE_AVAIL = ()
    UPDATE_CHECK = ()
    UPDATE_FAILED = ()
    UPDATE_FINISHED = ()
    UPDATE_LATEST = ()
    UPDATE_START = ()
    UPDATE_STOP = ()
    WARN_PERMISSION_ERROR = ()
    WARN_UNKNOWN_REMAINING_TIME = ()

class Msg:
    def __init__(self, msg_type, *data):
        self.type = msg_type
        self.data = data

