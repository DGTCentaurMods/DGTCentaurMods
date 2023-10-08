""" Handles config in the centaur.ini """

# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

import configparser

class Settings:
    """ Class handling config.ini """

    configfile = '/opt/DGTCentaurMods/config/centaur.ini'
    defconfigfile = '/opt/DGTCentaurMods/defaults/config/centaur.ini'

    @staticmethod
    def read(section, key, default = ''):
        """ Read a value from the key in the section """
        Settings.ensure_key_exists(section, key, default)
        config = configparser.ConfigParser()
        config.read(Settings.configfile)
        return config[section][key]

    @staticmethod
    def write(section, key, value, default = ''):
        """ Write a value to the key in the section """
        Settings.ensure_key_exists(section, key, default)
        config = configparser.ConfigParser()
        config.read(Settings.configfile)
        config.set(section, key, str(value))
        Settings.write_config(config)

    @staticmethod
    def delete(section, key):
        Settings.ensure_key_exists(section, key, '')
        config = configparser.ConfigParser()
        config.read(Settings.configfile)
        config.remove_option(section, key)
        Settings.write_config(config)

    @staticmethod
    def ensure_key_exists(section, key, default = ''):
        """ Ensures that the key exists in config.ini """
        config = configparser.ConfigParser()
        config.read(Settings.configfile)
        # First make sure the section is there
        if not config.has_section(section):
            config.add_section(section)
            Settings.write_config(config)
        # Then check if it has the key
        if not config.has_option(section, key):
            # If not then we want to get the value from defaults if we can
            defconfig = configparser.ConfigParser()
            defconfig.read(Settings.defconfigfile)
            value = ''
            if defconfig.has_section(section):                
                if defconfig.has_option(section, key):                    
                    value = defconfig[section][key]
            # If there's no default given then take the default in the parameter
            if value == '':
                value = default
            config.set(section, key, value)
            Settings.write_config(config)

    @staticmethod
    def get_config():
        config = configparser.ConfigParser()
        config.read(Settings.configfile)
        return config

    @staticmethod
    def write_config(config):
        """ Writes the config.ini """
        with open(Settings.configfile, 'w', encoding="utf-8") as f:
            config.write(f)
