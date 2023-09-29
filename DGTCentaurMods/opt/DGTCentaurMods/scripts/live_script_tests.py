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

# THIS SCRIPT CAN NOT BE DIRECLY EXECUTED
# PLEASE USE THE LIVE SCRIPT WEB EDITOR

# YOU CENTAUR BOARD NEEDS TO BE IN STARTING POSITION

from DGTCentaurMods.classes import LiveScript
from DGTCentaurMods.consts import Enums

import time, random

LS = LiveScript.get()

stage_id :str = None

def home():
    # Back to home menu
    LS.push_button(Enums.Btn.BACK)
    LS.push_button(Enums.Btn.BACK)
    LS.push_button(Enums.Btn.BACK)
    LS.push_button(Enums.Btn.BACK)

def resign():
    # Resign and quit the current module
    LS.push_button(Enums.Btn.UP)
    LS.waitfor_screen_text("Do you really want to resign?")
    LS.push_button(Enums.Btn.TICK)

def raise_exception(error:str):
    LS.write_text(4, stage_id)
    LS.write_text(5, "ERROR!")
    raise Exception(f'Stage "{stage_id}" -> {error}')

def play_random_move():
    legal_moves = LS.chessboard().legal_moves
    uci_move = str(random.choice(list(legal_moves)))[0:4]
    return LS.play(uci_move)

def play_or_die(uci_move:str):
    if not LS.play(uci_move):
        raise_exception(f'Unable to play "{uci_move}"!')


def stage_1vs1():

    home()

    # Choose PLAY/1VS1
    LS.select_menu("PLAY")
    LS.select_menu("PLAY 1 VS 1")

    # Start from fresh position
    LS.waitfor_fen_position()

    # Italian game
    play_or_die("e2e4 e7e5 g1f3 b8c6 f1c4")

    # Rollback
    LS.take_back(2)

    # Petrov trap
    play_or_die("g8f6 f3e5 f6e4 d1e2 e4f6 e5c6")

    # Rollback
    LS.take_back(7)

    # Go to promotion
    play_or_die("g2g4 a7a6 g4g5 a6a5 g5g6 a5a4 g6h7 a4a3 h7g8")

    # Choose the ROOK promotion
    LS.push_button(Enums.Btn.DOWN)

    play_or_die("a3b2 g8h8 b2c1")

    # Choose the QUEEN promotion
    LS.push_button(Enums.Btn.UP)

    play_or_die("h8h3 c1d1")

    if LS.chessboard().fen() != "rnbqkb2/1ppp1pp1/8/4p3/4P3/7R/P1PP1P1P/RN1qKBNR w KQq - 0 9":
        raise_exception("FEN is incorrect!")

def stage_randombot():
  
    home()

    # Choose PLUGINS
    LS.select_menu("PLUGINS")

    # Launch RandomBot
    LS.select_menu("RANDOM BOT")
    time.sleep(2)

    # Splash screen
    LS.push_button(Enums.Btn.PLAY)

    # Start from fresh position
    LS.waitfor_fen_position()

    # Random moves
    for _ in range(8):
        play_random_move()
        LS.play(LS.waitfor_computer_move())

def _stage_engine(id:str, conf:str):

    home()

    # Choose PLAY/ENGINE/LEVEL
    LS.select_menu("PLAY")
    LS.select_menu(id)
    LS.select_menu(conf)

    # Launch WHITE
    LS.push_button(Enums.Btn.TICK)

    # Start from fresh position
    LS.waitfor_fen_position()

    # Italian game
    play_or_die("e2e4")
    LS.play(LS.waitfor_computer_move())
    play_or_die("g1f3")
    LS.play(LS.waitfor_computer_move())
    play_or_die("f1c4")

    # Rollback
    LS.take_back(3)

    # Random moves
    for index in range(3):
        play_random_move()
        LS.write_text(4, "Random")
        LS.write_text(5, "move #"+str(index+1))
        LS.play(LS.waitfor_computer_move())

    # Trying with BLACK
    LS.push_button(Enums.Btn.BACK)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.TICK)

    # Engine loading...
    time.sleep(4)

    LS.play(LS.waitfor_computer_move())
    play_or_die("d7d5")
    LS.play(LS.waitfor_computer_move())
    play_or_die("e7e6")
    LS.play(LS.waitfor_computer_move())
    play_random_move()
    LS.play(LS.waitfor_computer_move())

    # Rollback
    LS.take_back(6)

    # Random moves
    for index in range(3):
        play_random_move()
        LS.write_text(4, "Random")
        LS.write_text(5, "move #"+str(index+1))
        LS.play(LS.waitfor_computer_move())

    LS.write_text(4, id)
    LS.write_text(5, "OK!")

    resign()

def stage_el_professor():

    home()

    # Choose PLUGINS
    LS.select_menu("PLUGINS")

    # Launch RandomBot
    LS.select_menu("EL PROFESSOR")
    time.sleep(2)

    # Splash screen
    # Expert mode
    LS.push_button(Enums.Btn.TICK)
    time.sleep(1)

    # White
    LS.push_button(Enums.Btn.UP)
    
    # Start from fresh position
    LS.waitfor_fen_position()

    time.sleep(3)

    # Wait for "Please find a good move" message
    LS.waitfor_screen_text("Please find a good move")

    play_or_die("d2d4")
    LS.waitfor_screen_text("YES")

    LS.play(LS.waitfor_computer_move())

    LS.waitfor_screen_text("Please find a good move")

    play_or_die("c2c4")
    LS.waitfor_screen_text("YES")

    LS.play(LS.waitfor_computer_move())
    LS.waitfor_screen_text("Please find a good move")
    
    if LS.play("c1g5"):
       raise Exception(f'c1g5 is not a correct move!')
    
    resign()

def stage_engines():

    global stage_id

    for args in (
       ("RODENTIV","Spassky"),
       ("MAIA","E-1200"),
       ("TEXEL","L-01"),
       ("WYLDCHESS","DRUNKEN"),
       ("GALJOEN","E-1500"),
       ("ZAHAK","E-1440"),
       ("STOCKFISH","E-1350"),
       ("CT800","E-1100")):

       stage_id = args[0]

       _stage_engine(args[0],args[1])
       time.sleep(2)

for stager in [
    stage_1vs1,
    stage_randombot,
    stage_el_professor,
    stage_engines,
]:
    stage_id = stager.__name__

    stager()

    LS.write_text(4, stage_id)
    LS.write_text(5, "OK")
    
    time.sleep(2)

LS.write_text(4, "ALL")
LS.write_text(5, "GOOD!")
