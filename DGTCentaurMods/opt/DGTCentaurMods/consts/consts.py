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

TAG_RELEASE = "ON23092901"

GITHUB_URI = "https://api.github.com/repos/Alistair-Crompton/DGTCentaurMods/releases/latest"
SOCKET_SERVER_URI = "https://alistair-centaur-mods-nodejs.adaptable.app"

HOME_DIRECTORY = str(Path.home())
OPT_DIRECTORY = f"/opt/{MAIN_ID}"
CONFIG_FILE = OPT_DIRECTORY + "/config/centaur.ini"

PLUGINS_DIRECTORY = OPT_DIRECTORY + "/plugins"
ENGINES_DIRECTORY = OPT_DIRECTORY + "/engines"
FAMOUS_DIRECTORY = OPT_DIRECTORY + "/famous_pgns"

WEB_NAME = MAIN_ID+" web "+TAG_RELEASE

LOG_NAME = MAIN_ID
LOG_DIRECTORY = HOME_DIRECTORY+"/logs"
LOG_FILENAME = f"{LOG_DIRECTORY}/{LOG_NAME}.log"
LOG_LEVEL = logging.DEBUG

VERBOSE_CHESS_ENGINE = False

BOARD_START_STATE = bytearray(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01')

FEN_LOG = HOME_DIRECTORY+"/centaur/fen.log"

FONT_FILE = OPT_DIRECTORY + "/resources/Typewriter Medium.ttf"
DIGITAL_FONT_FILE = OPT_DIRECTORY + "/resources/DIGITALDREAMFAT.ttf"
PACIFICO_FONT_FILE = OPT_DIRECTORY + "/resources/Pacifico.ttf"

#STOCKFISH_ENGINE_PATH = HOME_DIRECTORY+"/centaur/engines/stockfish_pi"
STOCKFISH_ENGINE_PATH = OPT_DIRECTORY+"/engines/stockfish"

EXTERNAL_REQUEST = "external_request"

EMPTY_LINE = ' '*20

SOUND_CORRECT_MOVES = "correct_moves"
SOUND_VERY_GOOD_MOVES = "very_good_moves"
SOUND_BAD_MOVES = "bad_moves"
SOUND_WRONG_MOVES = "wrong_moves"
SOUND_TAKEBACK_MOVES = "takeback_moves"
SOUND_COMPUTER_MOVES = "computer_moves"
SOUND_MUSIC = "starting_music"
SOUND_VICTORY = "victory_music"
SOUND_GAME_LOST= "game_lost_music"

SOUNDS_SETTINGS = [
    { "id":SOUND_MUSIC, "label":"Starting music" },
    { "id":SOUND_CORRECT_MOVES, "label":"Correct moves" },
    { "id":SOUND_WRONG_MOVES,"label":"Wrong moves" },
    { "id":SOUND_TAKEBACK_MOVES,"label":"Takebacks" },
    { "id":SOUND_COMPUTER_MOVES,"label":"Computer moves" },
    { "id":SOUND_VERY_GOOD_MOVES, "label":"Very good moves" },
    { "id":SOUND_BAD_MOVES, "label":"Bad moves" },
    { "id":SOUND_VICTORY,"label":"Victory music" },
    { "id":SOUND_GAME_LOST,"label":"Game lost/draw music" },
]