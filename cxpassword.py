#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("/lib/convert-x")

import cxpack
from cxutils import eprint
import json
import os
from simplecrypt import encrypt, decrypt

###############################################################################
__PASSWORD__ = "HangyaMaki"

def __encrypt_password(password):
    return encrypt(__PASSWORD__, password)

def __decrypt_password(encrypted):
    return decrypt(__PASSWORD__, encrypted)

###############################################################################

class PasswordManager:
    def __init__(self):
        self.__user = os.environ["USER"]
        if not os.path.exists(cxpack.config_dir):
            raise RuntimeError("The config directory is missing!!!")
        self.__password_file = os.path.join(cxpack.config_dir, "pass")
        self.__data = {}
        if os.path.exists(self.__password_file):
            self.__read()

    def save(self, password):
        self.__data[self.__user] = __encrypt_password(password)
        try:
            json.dump(self.__data, open(self.__password_file, 'w'))
        except IOError as e:
            eprint(e)

    def load(self):
        if self.__user in self.__data:
            return __decrypt_password(self.__data[self.__user])
        return None

    def __read(self):
        try:
            self.__data = json.load(open(self.__password_file))
        except IOError as e:
            eprint(e)




