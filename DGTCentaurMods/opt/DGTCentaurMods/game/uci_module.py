# Play any uci engine without DGT Centaur Adaptive Play
#
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

from DGTCentaurMods.game import game_manager
from DGTCentaurMods.display import epaper
from DGTCentaurMods.board import board

from random import randint

import time
import chess
import chess.engine
import sys
import pathlib
import configparser

#from lmnotify import LaMetricManager, Model, SimpleFrame, Sound;

# Expect the first argument to be 'white' 'black' or 'random' for what the player is playing
computer_color = {
     "white"  : chess.BLACK, 
     "black"  : chess.WHITE, 
     "random" : chess.WHITE if randint(0,1) == 1 else chess.BLACK }[sys.argv[1]]

# Arg2 is going to contain the name of our engine choice. We use this for database logging and to spawn the engine
engine_name = sys.argv[2]

uci_options_desc = "Default"
uci_options = {}

if engine_name == "stockfish":

    # Only for Stockfish
    engine_elo = sys.argv[3]
    engine = chess.engine.SimpleEngine.popen_uci(game_manager.HOME_DIRECTORY + "/centaur/engines/stockfish_pi")

    uci_options = {"UCI_LimitStrength": True, "UCI_Elo": engine_elo}

    engine_name = engine_name+'-'+engine_elo
else:

    engine = chess.engine.SimpleEngine.popen_uci(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/" + engine_name)

    if len(sys.argv) > 3:
        
        # This also has an options string...but what is actually passed in 3 is the desc which is the section name
        uci_options_desc = sys.argv[3]
        
        # These options we should derive form the uci file
        uci_file = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/" + engine_name + ".uci"
        
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(uci_file)

        for item in config.items(uci_options_desc):
            uci_options[item[0]] = item[1]

if uci_options != {}:
    options = uci_options
    engine.configure(options)

def key_callback(args):

    global exit_requested

    key = args["key"]

    if key == board.BTNBACK:
        engine.quit()
        board.ledsOff()
        exit_requested = True

    if key == board.BTNTICK:
        gm.show_evaluation = not gm.show_evaluation

        gm.update_evaluation()

        gm.display_board()
        gm.display_current_PGN()

    if key == board.BTNHELP:

        if gm.get_board().turn != computer_color:

            uci_move = gm.get_Stockfish_uci_move()

            from_num = game_manager.Converters.to_square_index(uci_move[0:2])
            to_num = game_manager.Converters.to_square_index(uci_move[2:4])

            board.ledFromTo(from_num,to_num)


def event_callback(args):

    # This function receives event callbacks about the game in play
    if "event" in args and args["event"] == game_manager.Event.PLAY:

        current_player = engine_name.capitalize() if gm.get_board().turn == computer_color else "You"

        epaper.writeText(1,f"{current_player} {'W' if gm.get_board().turn == chess.WHITE else 'B'}", font=game_manager.FONT_Typewriter)

        #sfengine = chess.engine.SimpleEngine.popen_uci("/home/pi/centaur/engines/stockfish_pi")
        #info = engine.analyse(gamemanager.cboard, chess.engine.Limit(time=0.5))
        #sfengine.quit()
        #evaluationGraphs(info)

        if gm.get_board().turn == computer_color:
            
            engine_move = engine.play(gm.get_board(), chess.engine.Limit(time=5), info=chess.engine.INFO_NONE)
            
            gm.set_computer_move(str(engine_move.move)) 


    if "termination" in args:
        # Termination.CHECKMATE
        # Termination.STALEMATE
        # Termination.INSUFFICIENT_MATERIAL
        # Termination.SEVENTYFIVE_MOVES
        # Termination.FIVEFOLD_REPETITION
        # Termination.FIFTY_MOVES
        # Termination.THREEFOLD_REPETITION
        # Termination.VARIANT_WIN
        # Termination.VARIANT_LOSS
        # Termination.VARIANT_DRAW

        epaper.writeText(1,' '+str(args["termination"])[12:], font=game_manager.FONT_Typewriter)


def move_callback(args):

    board.beep(board.SOUND_GENERAL)

    if "field_index" in args:
        board.led(args["field_index"])
    else:
        board.ledsOff()

    gm.update_Centaur_FEN()

    gm.display_board()
    gm.display_current_PGN()


# Activate the epaper
epaper.initEpaper()

statusbar = epaper.statusBar()
statusbar.start()

exit_requested = False

# Subscribe to the game manager
gm = game_manager.Factory(
     
    event_callback = event_callback,
    move_callback = move_callback,
    key_callback = key_callback,

    flags = game_manager.BoardOption.CAN_FORCE_MOVES | game_manager.BoardOption.CAN_UNDO_MOVES,
    
    game_informations = {
        "event" : uci_options_desc,
        "site"  : "",
        "round" : "",
        "white" : engine_name.capitalize() if computer_color == chess.WHITE else "Human",
        "black" : engine_name.capitalize() if computer_color == chess.BLACK else "Human",
    })

gm.start()

while exit_requested == False:
    time.sleep(0.1)

gm.stop()