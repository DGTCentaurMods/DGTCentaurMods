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

from DGTCentaurMods.game.consts import consts, Enums

from threading import Thread

import os, requests, subprocess, time, chess

class Singleton:
    _self = None

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self
    
def get_lastest_tag():
    response = requests.get("https://api.github.com/repos/Alistair-Crompton/DGTCentaurMods/releases/latest")

    # if file was downloaded
    if response.status_code == 200:
        response_json = response.json()
        latest_tag = response_json['tag_name']
        print(f"Latest tag found: {latest_tag}")
    else:
        print(f"Internet down? Status code: {response.status_code}")
        latest_tag = consts.TAG_RELEASE

    return latest_tag

def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]

def get_Centaur_FEN():

    try:
        f = open(consts.FEN_LOG, "r")
        fen = f.readline()
        f.close()

        return fen
    except:
        return chess.STARTING_FEN

def update_Centaur_FEN(fen):

    try:
        f = open(consts.FEN_LOG, "w")
        f.write(fen)
        f.close()
    except:
        pass


def delayed_command(command, delay):
    def _start_delayed(args, delay):
        time.sleep(delay)
        subprocess.run(args)

    t = Thread(target=_start_delayed, kwargs={'args': [{command}], 'delay': delay})
    t.start()
    
class Converters:

    @staticmethod
    def to_square_name(square) -> str:
        square_row = (square // 8)
        square_col = (square % 8)
        square_col = 7 - square_col
        return chr(ord("a") + (7 - square_col)) + chr(ord("1") + square_row)
        
    @staticmethod
    def to_square_index(uci_move, square_type = Enums.SquareType.ORIGIN) -> int:

        square_name = uci_move[0:2] if square_type == Enums.SquareType.ORIGIN else uci_move[2:4]
        
        square_col = ord(square_name[0:1]) - ord('a')
        square_row = ord(square_name[1:2]) - ord('1')

        return (square_row * 8) + square_col
