# -*- coding: utf-8 -*-
import sys
from enum import Enum

###############################################################################

def eprint(*args, **kwargs):
    """ print message to standard error"""
    print(*args, file=sys.stderr, **kwargs)

###############################################################################

class NoValue(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

class AutoNumber(NoValue):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

###############################################################################
