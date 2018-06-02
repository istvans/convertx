#!/usr/bin/python3
# -*- coding: utf-8 -*-
import cxpack
from cxutils import eprint
import os
###############################################################################

class ConfigManager():
    """ The configuration manager of conv2xvid """
    ### Public Methods ###
    def __init__(self):
        """ Read existing configuration or create the default """
        self.__cfg_file = os.path.join(cxpack.config_dir, "config.ini")
        self.__cfg = {}
        if not os.path.exists(cxpack.config_dir):
            os.makedirs(cxpack.config_dir, 0o700)
            self.__write_defaults()
        else:
            self.__read()
        # backward compatibility with < v0.1.0
        if "icon" not in self.__cfg:
            self.__write_defaults()
            self.__read()

    def set(self, key, value):
        """ Set a config element.
        Parameters
        ----------
        key : str
              The id of the config element
        value
              The new value of `key`
        """
        self.__cfg[key] = value
        self.__write()

    def get(self, key):
        """ Return the value of `key`
        Parameters
        ----------
        key : str
              The id of the config element
        """
        if key in self.__cfg:
            return self.__cfg[key]
        return None
    
    ### Private Methods ###
    
    def __read(self):
        """ Read the entire configuration """
        try:
            with open(self.__cfg_file) as config:
                for line in config:
                    key, value = tuple(line.split('='))
                    self.__cfg[key] = "".join(value.split())
        except IOError as e:
            eprint(e)
    
    def __write(self):
        """ Overwrite the entire configuration """
        try:
            with open(self.__cfg_file, 'w') as config:
                for key, value in self.__cfg.items():
                    config.write("{}={}\n".format(key, value))
        except IOError as e:
            eprint(e)

    def __write_defaults(self):
        self.__etc = "/etc"
        self.__readonly_dir = os.path.join(self.__etc, cxpack.package)
        self.__cfg["icon"] = os.path.join(self.__readonly_dir, "XviD.ico")
        self.__cfg["logo"] = os.path.join(self.__readonly_dir, "XviD_logo.png")
        self.__write()

