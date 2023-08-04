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

from DGTCentaurMods.game.classes import Log, GameFactory, CentaurScreen, CentaurBoard
from DGTCentaurMods.game.consts import Enums, fonts
from DGTCentaurMods.game.lib import common

import time, sys, chess

exit_requested = False

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

def main():

    def key_callback(args):

        assert "key" in args, "key_callback args needs to contain the 'key' entry!"

        global exit_requested

        key = args["key"]

        if key == CentaurBoard.BTNHELP:

            gfe.update_evaluation(force=True, text="thinking...")

            uci_move = gfe.get_Stockfish_uci_move()

            if uci_move!= None:
                from_num = common.Converters.to_square_index(uci_move, Enums.SquareType.ORIGIN)
                to_num = common.Converters.to_square_index(uci_move, Enums.SquareType.TARGET)

                CENTAUR_BOARD.led_from_to(from_num,to_num)

            gfe.update_evaluation()
            
            return True

        # Key has not been handled, Factory will handle it!
        return False


    def event_callback(args):

        assert "event" in args, "event_callback args needs to contain the 'event' entry!"

        global exit_requested

        if args["event"] == Enums.Event.QUIT:
            exit_requested = True

        if args["event"] == Enums.Event.PLAY:

            current_player = "White player" if gfe.get_board().turn else "Black player"

            SCREEN.write_text(1,f"{current_player} {'W' if gfe.get_board().turn == chess.WHITE else 'B'}", font=fonts.FONT_Typewriter_small, border=True)

    exit_requested = False

    # Subscribe to the game manager
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

    Log.debug(sys.argv)

    assert len(sys.argv)>1, "The first argument needs to be the PGN file!"

    main(sys.argv[1])