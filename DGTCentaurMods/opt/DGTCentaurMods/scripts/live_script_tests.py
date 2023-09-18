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

from DGTCentaurMods.classes import LiveScript, CentaurScreen
from DGTCentaurMods.consts import Enums

import time, random

SCREEN = CentaurScreen.get()
LS = LiveScript.get()

def home():
  # Back to home menu
  LS.push_button(Enums.Btn.BACK)
  LS.push_button(Enums.Btn.BACK)
  LS.push_button(Enums.Btn.BACK)
  LS.push_button(Enums.Btn.BACK)

def play_random_move():
  legal_moves = LS.chessboard().legal_moves
  uci_move = str(random.choice(list(legal_moves)))[0:4]
  return LS.play(uci_move)

def play_or_die(uci_move:str):
  if not LS.play(uci_move):
    SCREEN.write_text(5, "ERROR!")
    raise Exception(f'Unable to play "{uci_move}"!')



# Stage 1 - test 1vs1 module + promotion on both sides.
def stage_1vs1():

    home()

    # Choose PLAY/1VS1
    LS.push_button(Enums.Btn.TICK)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.TICK)
    time.sleep(2)

    # Italian game
    play_or_die("e2e4")
    play_or_die("e7e5")
    play_or_die("g1f3")
    play_or_die("b8c6")
    play_or_die("f1c4")

    # Rollback
    LS.take_back()
    LS.take_back()

    # Petrov trap
    play_or_die("g8f6")
    play_or_die("f3e5")
    play_or_die("f6e4")
    play_or_die("d1e2")
    play_or_die("e4f6")
    play_or_die("e5c6")

    # Rollback
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()

    # Go to promotion
    play_or_die("g2g4")
    play_or_die("a7a6")
    play_or_die("g4g5")
    play_or_die("a6a5")
    play_or_die("g5g6")
    play_or_die("a5a4")
    play_or_die("g6h7")
    play_or_die("a4a3")
    play_or_die("h7g8")

    # Choose the ROOK promotion
    LS.push_button(Enums.Btn.DOWN)

    play_or_die("a3b2")
    play_or_die("g8h8")
    play_or_die("b2c1")

    # Choose the QUEEN promotion
    LS.push_button(Enums.Btn.UP)

    play_or_die("h8h3")
    play_or_die("c1d1")

    assert LS.chessboard().fen() == "rnbqkb2/1ppp1pp1/8/4p3/4P3/7R/P1PP1P1P/RN1qKBNR w KQq - 0 9", "FEN is incorrect - stage 1."

    SCREEN.write_text(4, "STAGE 1")
    SCREEN.write_text(5, "OK!")

    time.sleep(2)


# Stage 2 - RandomBot.
# Random play against RandomBot
def stage_randombot():
  
    home()

    # Choose PLUGINS
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.TICK)

    # Launch RandomBot
    LS.push_button(Enums.Btn.TICK)
    LS.push_button(Enums.Btn.TICK)
    time.sleep(2)

    # Splash screen
    LS.push_button(Enums.Btn.PLAY)
    time.sleep(2)

    # Random moves
    for _ in range(8):
        play_random_move()
        LS.play(LS.waitfor_computer_move())

    SCREEN.write_text(4, "STAGE 2")
    SCREEN.write_text(5, "OK!")

    time.sleep(2)

def _stage_engine():

    # Launch WHITE
    LS.push_button(Enums.Btn.TICK)

    # Engine loading...
    time.sleep(4)

    # Italian game
    play_or_die("e2e4")
    LS.play(LS.waitfor_computer_move())
    play_or_die("g1f3")
    LS.play(LS.waitfor_computer_move())
    play_or_die("f1c4")

    # Rollback
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()

    # Forced moves
    # Petrov trap
    play_or_die("e7e5")
    play_or_die("g1f3")
    play_or_die("g8f6")
    play_or_die("f3e5")
    play_or_die("f6e4")
    play_or_die("d1e2")
    play_or_die("e4f6")
    play_or_die("e5c6")
    play_or_die("f8e7")
    play_or_die("c6d8")

    # Castle
    play_or_die("e8g8")

    play_or_die("e2e7")

    # Trying with BLACK
    LS.push_button(Enums.Btn.BACK)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.TICK)

    # Engine loading...
    time.sleep(4)

    LS.play(LS.waitfor_computer_move())
    play_or_die("d7d5")
    LS.play(LS.waitfor_computer_move())
    play_or_die("e7e5")
    LS.play(LS.waitfor_computer_move())
    play_or_die("g8f6")
    LS.play(LS.waitfor_computer_move())

    # Rollback
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()
    LS.take_back()

    # Forced moves
    # Petrov trap
    play_or_die("e2e4")
    play_or_die("e7e5")
    play_or_die("g1f3")
    play_or_die("g8f6")
    play_or_die("f3e5")
    play_or_die("f6e4")
    play_or_die("d1e2")
    play_or_die("e4f6")
    play_or_die("e5c6")


# Stage 3 - Maia.
def stage_Maia():

    home()

    # Choose PLAY/Maia-1200
    LS.push_button(Enums.Btn.TICK)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)

    LS.push_button(Enums.Btn.TICK)

    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.TICK)

    _stage_engine()

    SCREEN.write_text(4, "STAGE 3")
    SCREEN.write_text(5, "OK!")

    time.sleep(2)

# Stage 4 - Rodent IV.
def stage_RodentIV():

    home()

    # Choose PLAY/Rodent IV-Spassky
    LS.push_button(Enums.Btn.TICK)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)

    LS.push_button(Enums.Btn.TICK)

    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.DOWN)
    LS.push_button(Enums.Btn.TICK)

    _stage_engine()

    SCREEN.write_text(4, "STAGE 4")
    SCREEN.write_text(5, "OK!")

    time.sleep(2)

stage_1vs1()
stage_randombot()
stage_Maia()
stage_RodentIV()

SCREEN.write_text(4, "ALL")
SCREEN.write_text(5, "GOOD!")

