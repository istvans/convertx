#!/usr/bin/python3
# -*- coding: utf-8 -*-
from enum import Enum
# auto is not available... :/

###############################################################################

def auto():
    auto.__counter += 1
    return auto.__counter
auto.__counter = 0

###############################################################################

class Type(Enum):
    PREP = auto()
    START = auto()
    STOP = auto()
    STOP_ACK = auto()
    CLOSE = auto()
    CLOSE_ACK = auto()
    CONV = auto()
    STEP = auto()
    ELAPSED = auto()
    LEFT = auto()
    DELETE = auto()
    SET_CFG = auto()
    INPUT_FILE = auto()
    OUTPUT_FILE = auto()
    FINISHED = auto()
    UPDATE_CHECK = auto()
    UPDATE_AVAIL = auto()
    UPDATE_START = auto()
    UPDATE_FINISHED = auto()
    WARN_UNKNOWN_REMAINING_TIME = auto()

class Msg:
    def __init__(self, msg_type, *data):
        self.type = msg_type
        self.data = data

