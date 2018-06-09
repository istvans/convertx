# -*- coding: utf-8 -*-
import random
from simplecrypt import encrypt, decrypt
import string

###############################################################################

class Password:
    """ Store encrypted password """
    __gem = ''.join(random.SystemRandom().choice(string.ascii_uppercase
        + string.digits) for _ in range(16))

    def __init__(self, raw_password):
        self.__password = None
        self.set(raw_password)

    def __bool__(self):
        return bool(self.__password)

    def set(self, raw_password):
        if raw_password:
            self.__password = encrypt(Password.__gem, raw_password)

    def get(self):
        if not self.__password:
            return None
        return decrypt(Password.__gem, self.__password).decode("utf-8") 
