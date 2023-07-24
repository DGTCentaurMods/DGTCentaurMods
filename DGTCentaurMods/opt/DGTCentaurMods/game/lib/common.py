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

from DGTCentaurMods.game.consts import consts, Enums

import configparser

def get_Centaur_FEN():

    try:
        f = open(consts.FENLOG, "r")
        fen = f.readline()
        f.close()

        return fen
    except:
        return None

def update_Centaur_FEN(fen):

    try:
        f = open(consts.FENLOG, "w")
        f.write(fen)
        f.close()
    except:
        pass

def update_last_uci_command(command):

    # TODO: initial centaur.py script needs a full rewrite
    try:
        # Get the config
        conf = configparser.ConfigParser()
        conf.read_dict({'system':{ 'last_uci': ''}})
        conf.read(consts.CONFIG_FILE)
        conf.set('system', 'last_uci', command)
    
        with open(consts.CONFIG_FILE, 'w') as f:
            conf.write(f)
    except:
        pass

def get_last_uci_command():

    # TODO: initial centaur.py script needs a full rewrite
    try:
         # Get the config
        conf = configparser.ConfigParser()
        conf.read_dict({'system':{ 'last_uci': ''}})
        conf.read(consts.CONFIG_FILE)

        return conf.get('system', 'last_uci')
    except:
        pass
    
    return None
    
class Converters:

    @staticmethod
    def to_square_name(square) -> str:
        square_row = (square // 8)
        square_col = (square % 8)
        square_col = 7 - square_col
        return chr(ord("a") + (7 - square_col)) + chr(ord("1") + square_row)
        
    @staticmethod
    def to_square_index(uci_move, square_type) -> int:

        square_name = uci_move[0:2] if square_type == Enums.SquareType.ORIGIN else uci_move[2:4]
        
        square_col = ord(square_name[0:1]) - ord('a')
        square_row = ord(square_name[1:2]) - ord('1')

        return (square_row * 8) + square_col
