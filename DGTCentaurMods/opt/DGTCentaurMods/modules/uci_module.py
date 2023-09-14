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

from DGTCentaurMods.classes import ChessEngine, GameFactory, Log, CentaurBoard, CentaurScreen
from DGTCentaurMods.classes.CentaurConfig import CentaurConfig
from DGTCentaurMods.consts import consts, Enums
from DGTCentaurMods.lib import common

from random import randint

import sys, time, chess, configparser

#from lmnotify import LaMetricManager, Model, SimpleFrame, Sound;

exit_requested = False

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

def main(color, engine_name, engine_parameters):

    global exit_requested

    exit_requested = False

    computer_color = {
        "white"  : chess.BLACK, 
        "black"  : chess.WHITE, 
        "random" : chess.WHITE if randint(0,1) == 1 else chess.BLACK }[color]

    # If computer is white, we reverse the screen
    SCREEN.set_reversed(computer_color)

    CentaurConfig.update_last_uci_command(("black" if computer_color else "white")+' '+engine_name+' "'+engine_parameters+'"')

    uci_options_desc = "Default"
    uci_options = {}

    # Async chess engine result
    # The result should never be outdated since we test it before trigerring the callback...
    def on_computer_move_done(result):
        if result != None:
            gfe.set_computer_move(str(result.move))

    engine = ChessEngine.get(f"{consts.OPT_DIRECTORY}/engines/{engine_name}")

    if len(engine_parameters) > 3:
        
        # This also has an options string...but what is actually passed in 3 is the desc which is the section name
        uci_options_desc = engine_parameters
        
        # These options we should derive form the uci file
        uci_file = f"{consts.OPT_DIRECTORY}/engines/{engine_name}.uci"
        
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(uci_file)

        for item in config.items(uci_options_desc):
            uci_options[item[0]] = item[1]

        engine_name = common.capitalize_string(engine_name)+'-'+uci_options_desc


    engine.configure(uci_options)

    def key_callback(args):

        assert "key" in args, "key_callback args needs to contain the 'key' entry!"

        key = args["key"]

        if key == Enums.Btn.HELP:

            if gfe.get_board().turn != computer_color:
                gfe.flash_hint()
            
            return True

        # Key has not been handled, Factory will handle it!
        return False


    def event_callback(args):

        assert "event" in args, "event_callback args needs to contain the 'event' entry!"

        global exit_requested

        if args["event"] == Enums.Event.QUIT:
            exit_requested = True

        if args["event"] == Enums.Event.TERMINATION:

            if args["outcome"].winner == (not computer_color):
                CENTAUR_BOARD.beep(Enums.Sound.VICTORY)
            else:
                CENTAUR_BOARD.beep(Enums.Sound.GAME_LOST)

        if args["event"] == Enums.Event.PLAY:

            current_player = engine_name if gfe.get_board().turn == computer_color else "You"

            gfe.display_board_header(f"{current_player} {'W' if gfe.get_board().turn == chess.WHITE else 'B'}")

            gfe.send_to_web_clients({ 
                "turn_caption":f"turn → {current_player} ({'WHITE' if gfe.get_board().turn == chess.WHITE else 'BLACK'})"
            })

            if gfe.get_board().turn == computer_color:
                
                # Async request
                engine.play(
                    gfe.get_board(), 
                    chess.engine.Limit(time=5), 
                    info=chess.engine.INFO_NONE, 
                    on_taskengine_done = on_computer_move_done)

    def move_callback(args):

        # field_index, san_move, uci_move are available
        assert "uci_move" in args, "args needs to contain 'uci_move' key!"
        assert "san_move" in args, "args needs to contain 'san_move' key!"
        assert "field_index" in args, "args needs to contain 'field_index' key!"

        # Move is accepted!
        return True

    def undo_callback(args):

        # field_index, san_move, uci_move are available
        assert "uci_move" in args, "args needs to contain 'uci_move' key!"
        assert "san_move" in args, "args needs to contain 'san_move' key!"
        assert "field_index" in args, "args needs to contain 'field_index' key!"

        return

    # Subscribe to the game factory
    gfe = GameFactory.Engine(
        
        event_callback = event_callback,
        move_callback = move_callback,
        undo_callback = undo_callback,
        key_callback = key_callback,

        chess_engine = engine,

        flags = Enums.BoardOption.CAN_FORCE_MOVES | Enums.BoardOption.CAN_UNDO_MOVES,
        
        game_informations = {
            "event" : uci_options_desc,
            "site"  : "",
            "round" : "",
            "white" : engine_name.capitalize() if computer_color == chess.WHITE else "Human",
            "black" : engine_name.capitalize() if computer_color == chess.BLACK else "Human",
        })

    gfe.start()

    while exit_requested == False:
        time.sleep(.1)

if __name__ == '__main__':

    Log.debug(sys.argv)

    assert len(sys.argv)>1, "The first argument needs to be 'white' 'black' or 'random' for what the player is playing!"
    assert len(sys.argv)>2, "The second argument needs to be the engine name!"
    assert len(sys.argv)>3, "The third argument needs to be the engine parameter!"

    # Arg2 is going to contain the name of our engine choice. We use this for database logging and to spawn the engine
    engine_name = sys.argv[2]

    engine_parameters = sys.argv[3]

    main(sys.argv[1], engine_name, engine_parameters)