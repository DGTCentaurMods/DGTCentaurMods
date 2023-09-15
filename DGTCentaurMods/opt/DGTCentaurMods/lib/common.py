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

from DGTCentaurMods.classes import Log
from DGTCentaurMods.consts import consts, Enums

from threading import Thread

import os, requests, subprocess, time, chess

class Singleton:
    """Classes derived from Singleton only ever have one instance

    >>> class Derived(Singleton):
    ...     pass
    >>> ref1 = Derived()
    >>> ref2 = Derived()
    >>> ref1 is ref2
    True
    """

    _self = None

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

def get_lastest_tag() -> str:

    try:
        response = requests.get("https://api.github.com/repos/Alistair-Crompton/DGTCentaurMods/releases/latest")

        # if file was downloaded
        if response.status_code == 200:
            response_json = response.json()
            latest_tag = response_json['tag_name']
            print(f"Latest tag found: {latest_tag}")
        else:
            print(f"Internet down? Status code: {response.status_code}")
            latest_tag = consts.TAG_RELEASE
    except:
        latest_tag = consts.TAG_RELEASE
        pass

    return latest_tag

def capitalize_string(str: str) -> str:
    """Capitalize first letter of string, preserving existing capitals

    >>> capitalize_string("my Turn")
    'My Turn'

    Note this differs from the built-in str.capitalize() method
    >>> "my Turn".capitalize()
    'My turn'
    """
    return str[:1].upper()+str[1:]

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

def get_Centaur_FEN() -> str:
    """Read board state from FEN log (default ~/centaur/fen.log),
    returning default starting position if log does not exist."""

    try:
        with open(consts.FEN_LOG, "r") as f:
            fen = f.readline()
        return fen
    except:
        return chess.STARTING_FEN

def update_Centaur_FEN(fen: str) -> None:
    """Save board state to FEN log (default ~/centaur/fen.log)"""

    try:
        # TODO Most likely cause of failure here is that the log directory
        # does not exist.  Should we create it?
        # >>> os.makedirs(os.path.dirname(consts.FEN_LOG), exist_ok=True)
        with open(consts.FEN_LOG, "w") as f:
            f.write(fen)
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
    def fen_to_board_state(fen : str) -> bytearray:

        EMPTY_FEN = "8/8/8/8/8/8/8/8 w - - 0 1"

        try:
            result : bytearray = [0] * 64

            fen = (fen or EMPTY_FEN).replace('/', '')

            for index in range(1,9):
                fen = fen.replace(str(index), ' '*index)

            for a in range(8,0,-1):
                for b in range(0,8):
                    index = ((a-1)*8)+b
                    if fen[index] != ' ':
                        result[index] = 1

            return result

        except Exception as e:
            Log.debug(f"fen:{fen}")
            Log.exception(Converters.fen_to_board_state, e)
            pass

    @staticmethod
    def to_square_name(square: chess.Square) -> str:
        """Return the algebraic name of the indexed square

        >>> Converters.to_square_name(0)
        'a1'
        >>> Converters.to_square_name(27)
        'd4'
        """

        return chess.square_name(square)

    @staticmethod
    def to_square_index(uci_move: str, square_type = Enums.SquareType.ORIGIN) -> chess.Square:
        """Find the origin or target index of a UCI move or a square

        >>> Converters.to_square_index("g1f3", Enums.SquareType.ORIGIN)
        6
        >>> Converters.to_square_index("g1f3", Enums.SquareType.TARGET)
        21
        >>> Converters.to_square_index("a1", Enums.SquareType.ORIGIN)
        0

        """

        square_name = uci_move[0:2] if square_type == Enums.SquareType.ORIGIN else uci_move[2:4]
        
        square_col = ord(square_name[0:1]) - ord('a')
        square_row = ord(square_name[1:2]) - ord('1')

        return (square_row * 8) + square_col


