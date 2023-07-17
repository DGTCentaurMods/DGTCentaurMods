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

from DGTCentaurMods.game.classes import GameFactory, Log
from DGTCentaurMods.game.consts import Enums, fonts
from DGTCentaurMods.game.lib import common

from DGTCentaurMods.display import epaper
from DGTCentaurMods.board import board

import pathlib
import random
import time
import chess
import chess.engine
import chess.pgn
import sys
import os

assert len(sys.argv)>1, "The first argument needs to be the PGN file!"

FAMOUS_PGNS_DIR = str(pathlib.Path(__file__).parent.resolve()) + "/famous_pgns/"
MAX_RETRIES = 2
AUTO_MOVES_COUNT = 4

ERROR_MESSAGES = (
    "wrong move!",
    "bad move!",
    "try again!")

retry_count = MAX_RETRIES

# Expect the first argument to be the PGN file name
pgn_file = FAMOUS_PGNS_DIR+sys.argv[1]

if not os.path.exists(pgn_file):
    Log.exception(f"'{pgn_file}' does not exist!")
    exit()

try:
    pgn = open(pgn_file)

    # We only read the first game of the file
    game = chess.pgn.read_game(pgn)

except Exception as e:
    Log.exception(f"PGN error:{e}")
    exit()

Log.debug(game.headers)

assert "Event" in game.headers, "PGN header needs to contain 'Event' section!"
assert "White" in game.headers, "PGN header needs to contain 'White' section!"
assert "Black" in game.headers, "PGN header needs to contain 'Black' section!"
assert "Player" in game.headers, "PGN header needs to contain 'Player' section!"

player_names = { "white":game.headers["White"], "black":game.headers["Black"], }
human_color = chess.WHITE if game.headers["Player"] == "White" else chess.BLACK

Log.debug(f"human_color={human_color}")

moves_history = tuple(game.mainline_moves())
current_index = 0

assert len(moves_history)>10, f"PGN must count at least 10 moves! (has {len(moves_history)})"

def show_uci_move_on_board(uci_move):
    from_num = common.Converters.to_square_index(uci_move, Enums.SquareType.ORIGIN)
    to_num = common.Converters.to_square_index(uci_move, Enums.SquareType.TARGET)

    board.ledFromTo(from_num,to_num)

def key_callback(args):

    assert "key" in args, "key_callback args needs to contain the 'key' entry!"

    global exit_requested

    key = args["key"]

    if key == board.BTNUP:

        global retry_count

        correct_uci_move = moves_history[current_index].uci().strip()
        retry_count=0
        show_uci_move_on_board(correct_uci_move)

        return True

    if key == board.BTNHELP:

        if gfe.get_board().turn == human_color:

            gfe.update_evaluation(force=True, text="thinking...")

            uci_move = gfe.get_Stockfish_uci_move()

            if uci_move!= None:
                show_uci_move_on_board(uci_move)

            gfe.update_evaluation()

        return True
    
    # Key has not been handled, Factory will handle it!
    return False


def event_callback(args):

    assert "event" in args, "event_callback args needs to contain the 'event' entry!"

    global current_index
    global exit_requested

    if args["event"] == Enums.Event.QUIT:
        exit_requested = True

    if args["event"] == Enums.Event.NEW_GAME:
        current_index = 0

        epaper.writeText(9.5,game.headers["Event"], font=fonts.FONT_Typewriter_small, border=True, align_center=True)
        epaper.writeText(11,game.headers["White"], font=fonts.FONT_Typewriter_small, border=True, align_center=True)
        epaper.writeText(12,game.headers["Black"], font=fonts.FONT_Typewriter_small, border=True, align_center=True)
        epaper.writeText(13,"You play "+("white" if human_color else "black")+"!", font=fonts.FONT_Typewriter_small, border=True, align_center=True)
        
    if args["event"] == Enums.Event.PLAY:

        current_player = player_names["white"].capitalize() if gfe.get_board().turn else player_names["black"].capitalize()

        epaper.writeText(1,f"{current_player} {'W' if gfe.get_board().turn == chess.WHITE else 'B'}", font=fonts.FONT_Typewriter_small, border=True, align_center=True)

        # We show the opponent moves and the first moves
        if gfe.get_board().turn != human_color or current_index<AUTO_MOVES_COUNT:

            uci_move = moves_history[current_index].uci().strip()

            time.sleep(.5)

            show_uci_move_on_board(uci_move)


def move_callback(args):

    global current_index
    global retry_count

    # field_index, san_move, uci_move are available
    assert "uci_move" in args, "args needs to contain 'uci_move' key!"
    assert "san_move" in args, "args needs to contain 'san_move' key!"
    assert "field_index" in args, "args needs to contain 'field_index' key!"

    uci_move = args["uci_move"]
    field_index = args["field_index"]

    correct_uci_move = moves_history[current_index].uci().strip()

    success = correct_uci_move == uci_move

    if not success:
        board.beep(board.SOUND_WRONG_MOVE)

        if current_index<AUTO_MOVES_COUNT or gfe.get_board().turn == human_color:
            # We do nothing...
            pass
        else:
            if retry_count==0:
                show_uci_move_on_board(correct_uci_move)
            else:
                gfe.update_evaluation(force=True, text=random.choice(ERROR_MESSAGES))
                retry_count = retry_count -1
                board.led(field_index)

    else:
        current_index = current_index +1
        retry_count = MAX_RETRIES

    return success

def undo_callback(args):

    global current_index

    # field_index, san_move, uci_move are available
    assert "uci_move" in args, "args needs to contain 'uci_move' key!"
    assert "san_move" in args, "args needs to contain 'san_move' key!"
    assert "field_index" in args, "args needs to contain 'field_index' key!"

    current_index = current_index -1

    return


# Activate the epaper
epaper.initEpaper()

statusbar = epaper.statusBar()
statusbar.start()
statusbar.print()

exit_requested = False

# Subscribe to the game manager
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