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

from DGTCentaurMods.classes import GameFactory, Log, CentaurBoard, CentaurScreen
from DGTCentaurMods.consts import Enums, consts
from DGTCentaurMods.lib import common

import random
import time
import chess
import chess.pgn
import sys
import os

from typing import Optional

exit_requested = False

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

MAX_RETRIES = 2
AUTO_MOVES_COUNT = 4

ERROR_MESSAGES = (
    "wrong move!",
    "bad move!",
    "try again!")

retry_count = MAX_RETRIES
current_index = 0

def main(pgn):

    global current_index
    global exit_requested

    exit_requested = False

    # Expect the first argument to be the PGN file name
    pgn_file = consts.FAMOUS_DIRECTORY+'/'+pgn

    if not os.path.exists(pgn_file):
        Log.exception(main, f"'{pgn_file}' does not exist!")
        exit()

    try:
        pgn = open(pgn_file)

        # We only read the first game of the file
        game = chess.pgn.read_game(pgn)

    except Exception as e:
        Log.exception(main, e)
        exit()

    Log.debug(game.headers)

    assert "Event" in game.headers, "PGN header needs to contain 'Event' section!"
    assert "White" in game.headers, "PGN header needs to contain 'White' section!"
    assert "Black" in game.headers, "PGN header needs to contain 'Black' section!"
    assert "Player" in game.headers, "PGN header needs to contain 'Player' section!"

    player_names = { "white":game.headers["White"], "black":game.headers["Black"], }
    human_color = chess.WHITE if game.headers["Player"] == "White" else chess.BLACK

    # If human is black, we reverse the screen
    SCREEN.set_reversed(not human_color)

    Log.debug(f"human_color={human_color}")

    moves_history = tuple(game.mainline_moves())


    assert len(moves_history)>10, f"PGN must count at least 10 moves! (has {len(moves_history)})"

    def show_uci_move_on_board(uci_move):
        from_num = common.Converters.to_square_index(uci_move, Enums.SquareType.ORIGIN)
        to_num = common.Converters.to_square_index(uci_move, Enums.SquareType.TARGET)

        CENTAUR_BOARD.led_from_to(from_num,to_num)

    def key_callback(key:Enums.Btn):

        if key == Enums.Btn.UP:

            global retry_count

            correct_uci_move = moves_history[current_index].uci().strip()
            retry_count=0
            show_uci_move_on_board(correct_uci_move)

            gfe.send_message_to_web_ui({ 
                "clear_board_graphic_moves":False,
                "tip_uci_move":correct_uci_move,
            })

            return True

        if key == Enums.Btn.HELP:

            if gfe.chessboard.turn == human_color:
                gfe.flash_hint()

            return True
        
        # Key has not been handled, Factory will handle it!
        return False


    def event_callback(event:Enums.Event, outcome:Optional[chess.Outcome]):

        global current_index
        global exit_requested

        if event == Enums.Event.QUIT:
            exit_requested = True

        if event == Enums.Event.NEW_GAME:
            current_index = 0

            SCREEN.write_text(9.5,game.headers["Event"], bordered=True)
            SCREEN.write_text(11,game.headers["White"], bordered=True)
            SCREEN.write_text(12,game.headers["Black"], bordered=True)
            SCREEN.write_text(13,"You play "+("white" if human_color else "black")+"!", bordered=True)
            
        if event == Enums.Event.PLAY:

            current_player = player_names["white"].capitalize() if gfe.chessboard.turn else player_names["black"].capitalize()

            gfe.display_board_header(f"{current_player} {'W' if gfe.chessboard.turn == chess.WHITE else 'B'}")

            gfe.send_message_to_web_ui({ 
                "turn_caption":f"turn → {current_player} ({'WHITE' if gfe.chessboard.turn == chess.WHITE else 'BLACK'})"
            })

            # We show the opponent moves and the first moves
            if gfe.chessboard.turn != human_color or current_index<AUTO_MOVES_COUNT:

                uci_move = moves_history[current_index].uci().strip()

                time.sleep(.5)

                show_uci_move_on_board(uci_move)

                gfe.send_message_to_web_ui({ 
                    "clear_board_graphic_moves":False,
                    "computer_uci_move":uci_move,
                })


    def move_callback(uci_move:str, san_move:str, color:chess.Color, field_index:chess.Square):

        global current_index
        global retry_count

        correct_uci_move = moves_history[current_index].uci().strip()

        success = correct_uci_move == uci_move

        if not success:
            CENTAUR_BOARD.beep(Enums.Sound.WRONG_MOVE)

            if current_index<AUTO_MOVES_COUNT or gfe.chessboard.turn == human_color:
                # We do nothing...
                pass
            else:
                if retry_count==0:
                    show_uci_move_on_board(correct_uci_move)

                    gfe.send_message_to_web_ui({ 
                        "clear_board_graphic_moves":False,
                        "tip_uci_move":correct_uci_move,
                    })
                else:
                    gfe.update_evaluation(force=True, text=random.choice(ERROR_MESSAGES))
                    retry_count = retry_count -1
                    CENTAUR_BOARD.led(field_index)

        else:
            current_index = current_index +1
            retry_count = MAX_RETRIES

        return success

    def undo_callback(uci_move:str, san_move:str, field_index:chess.Square):

        global current_index
        current_index = current_index -1

        return

    exit_requested = False

    # Subscribe to the game factory
    gfe = GameFactory.Engine(
        
        event_callback = event_callback,
        move_callback = move_callback,
        key_callback = key_callback,
        undo_callback = undo_callback,

        flags = Enums.BoardOption.DB_RECORD_DISABLED | Enums.BoardOption.CAN_UNDO_MOVES,
        
    )

    gfe.start()

    while exit_requested == False:
        time.sleep(0.1)

if __name__ == '__main__':

    Log.debug(sys.argv)

    assert len(sys.argv)>1, "The first argument needs to be the PGN file!"

    main(sys.argv[1])


