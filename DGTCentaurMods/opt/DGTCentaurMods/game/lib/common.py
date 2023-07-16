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

from DGTCentaurMods.game.classes import Log
from DGTCentaurMods.game.consts import consts
from DGTCentaurMods.board import board



# Get the config
__conf = board.conf

def get_Centaur_FEN():

    try:
        Log.debug("Reading Centaur FEN...")

        f = open(consts.FENLOG, "r")
        fen = f.readline()
        f.close()

        return fen
    except:
        return None

def update_Centaur_FEN(fen):

    Log.debug("Updating Centaur FEN...")

    f = open(consts.FENLOG, "w")
    f.write(fen)
    f.close()

def update_last_uci_command(command):

    Log.debug("Updating last uci command...")

    __conf.update_value('system','last_uci',command)

def get_last_uci_command():

    try:
        Log.debug("Reading last uci command...")

        command = __conf.read_value('system', 'last_uci')

        return command
    except:
        return None