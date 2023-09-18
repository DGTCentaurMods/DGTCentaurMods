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

from DGTCentaurMods.classes import GameFactory, CentaurScreen, CentaurBoard
from DGTCentaurMods.classes.CentaurConfig import CentaurConfig
from DGTCentaurMods.consts import Enums
from DGTCentaurMods.lib import common

from typing import Optional

import time, chess

exit_requested = False

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

def main():

    global exit_requested

    exit_requested = False

    CentaurConfig.update_last_uci_command("1vs1_module")

    def key_callback(key:Enums.Btn):

        if key == Enums.Btn.HELP:
            gfe.flash_hint()
            
            return True

        # Key has not been handled, Factory will handle it!
        return False


    def event_callback(event:Enums.Event, outcome:Optional[chess.Outcome]):

        global exit_requested

        if event == Enums.Event.QUIT:
            exit_requested = True

        if event== Enums.Event.PLAY:

            current_player = "White player" if gfe.chessboard.turn else "Black player"

            gfe.display_board_header(f"{current_player} {'W' if gfe.chessboard.turn == chess.WHITE else 'B'}")

    exit_requested = False


    # Subscribe to the game factory
    gfe = GameFactory.Engine(
        
        event_callback = event_callback,
        key_callback = key_callback,

        flags = Enums.BoardOption.CAN_FORCE_MOVES | Enums.BoardOption.CAN_UNDO_MOVES,
        
        game_informations = {
            "event" : "Human vs human",
            "site"  : "",
            "round" : "",
            "white" : "Human 1",
            "black" : "Human 2",
        })

    gfe.start()

    while exit_requested == False:
        time.sleep(0.1)

if __name__ == '__main__':

    main()