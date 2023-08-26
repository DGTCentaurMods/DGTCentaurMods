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

import logging

from pathlib import Path

MAIN_ID = "DGTCentaurMods"

HOME_DIRECTORY = str(Path.home())
OPT_DIRECTORY = f"/opt/{MAIN_ID}"
CONFIG_FILE = OPT_DIRECTORY + "/config/centaur.ini"

WEB_NAME = MAIN_ID+" web 2.0"

LOG_NAME = MAIN_ID
LOG_DIRECTORY = HOME_DIRECTORY+"/logs"
LOG_FILENAME = f"{LOG_DIRECTORY}/{LOG_NAME}.log"
LOG_LEVEL = logging.DEBUG

BOARD_START_STATE = bytearray(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01')

FEN_LOG = HOME_DIRECTORY+"/centaur/fen.log"

FONT_FILE = OPT_DIRECTORY + "/resources/Typewriter Medium.ttf"

STOCKFISH_ENGINE_PATH = HOME_DIRECTORY+"/centaur/engines/stockfish_pi"


SOUND_CORRECT_MOVES = "correct_moves"
SOUND_WRONG_MOVES = "wrong_moves"
SOUND_TAKEBACK_MOVES = "takeback_moves"
SOUND_COMPUTER_MOVES = "computer_moves"
SOUND_MUSIC = "starting_music"

SOUNDS_SETTINGS = [
    { "id":SOUND_MUSIC, "label":"Starting music" },
    { "id":SOUND_CORRECT_MOVES, "label":"Correct moves" },
    { "id":SOUND_WRONG_MOVES,"label":"Wrong moves" },
    { "id":SOUND_TAKEBACK_MOVES,"label":"Takebacks" },
    { "id":SOUND_COMPUTER_MOVES,"label":"Computer moves" }]