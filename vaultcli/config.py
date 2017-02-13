#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © Adrián López Tejedor <adrianlzt@gmail.com>
#             2016 Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

import configparser

class Config(object):
    """
    Class for work with config
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file)
        except Exception as e:
            err = 'vaultcli config file is corrupted.\n{0}'.format(e)
            raise SystemExit(err)

    def get(self, section, option):
        """
        Returns a config option value from config file

        :param section: section where the option is stored
        :param option: option name
        :return: a config option value
        :rtype: string
        """
        return self.config.get(section, option, fallback=None)

    def set(self, section, option, value):
        """
        Set a config option value into config file

        :param section: section where the option is stored
        :param option: option name
        :param value: option value
        """
        if section != 'DEFAULT' and not self.config.has_section(section):
            self.config[section] = {}
        self.config[section][option] = value
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            err = 'vaultcli cannot write in config file.\n{0}'.format(e)
            raise SystemExit(err)

    def get_default(self, option):
        """
        Returns a config option value into default section of config file

        :param option: option name
        :return: a config option value
        :rtype: string
        """
        return self.get('DEFAULT', option)

    def set_default(self, option, value):
        """
        Set a config option value into default section of config file

        :param option: option name
        :param value: option value
        """
        self.set('DEFAULT', option, value)
