# -*- coding: utf-8 -*-
import sys

###############################################################################

def eprint(*args, **kwargs):
    """ print message to standard error"""
    print(*args, file=sys.stderr, **kwargs)

###############################################################################
