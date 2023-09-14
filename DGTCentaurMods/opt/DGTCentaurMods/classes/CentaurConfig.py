# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
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
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.consts import consts

import configparser, json


class CentaurConfig:

    @staticmethod
    def _update(section:str, id:str, value:str, default_value:str):

        try:
            # Get the config
            conf = configparser.ConfigParser()
            conf.read_dict({section:{ id: default_value}})
            conf.read(consts.CONFIG_FILE)
            conf.set(section, id, value)
        
            with open(consts.CONFIG_FILE, 'w') as f:
                conf.write(f)
        except:
            pass

    @staticmethod
    def _get(section:str, id:str, default_value:str):

        try:
            # Get the config
            conf = configparser.ConfigParser()
            conf.read_dict({section:{ id: default_value }})
            conf.read(consts.CONFIG_FILE)

            return conf.get(section, id)
        except:
            pass
        
        return None
    
    @staticmethod
    def update_system_settings(id:str, value:str) -> None:
        CentaurConfig._update('system', id, value, '')

    @staticmethod
    def get_system_settings(id:str, default:str) -> str:
        return CentaurConfig._get('system', id, default)

    @staticmethod
    def update_sound_settings(id:str, value:bool) -> None:
        CentaurConfig._update('sounds', id, '1' if value else '0', '1')

    @staticmethod
    def get_sound_settings(id:str)  -> bool:
        return CentaurConfig._get('sounds', id, '1') == '1'

    @staticmethod
    def update_lichess_settings(id:str, value:str) -> None:
        CentaurConfig._update('lichess', id, value, '')

    @staticmethod
    def get_lichess_settings(id:str) -> str:
        return CentaurConfig._get('lichess', id, '')

    @staticmethod
    def update_last_uci_command(command:str) -> None:
        CentaurConfig._update('system', 'last_uci', command, '')

    @staticmethod
    def get_last_uci_command() -> str:
        return CentaurConfig._get('system', 'last_uci', '')
    
    @staticmethod
    def update_lichess_seeking_params(params:dict) -> None:
        CentaurConfig._update('lichess', 'seeking_params', json.dumps(params), '[]')

    @staticmethod
    def get_lichess_seeking_params() -> ():
        return tuple(json.loads(CentaurConfig._get('lichess', 'seeking_params', '[]')))