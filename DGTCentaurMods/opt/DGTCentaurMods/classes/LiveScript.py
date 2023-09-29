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

from DGTCentaurMods.classes import Log, GameFactory, CentaurBoard, CentaurScreen, SocketClient
from DGTCentaurMods.lib import common
from DGTCentaurMods.consts import Enums, fonts

import types, threading, time
from typing import Optional

import chess

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()
SOCKET = SocketClient.connect_local_server()

class _api():

    _game_engine:Optional[GameFactory.Engine] = None

    @staticmethod
    def _debug(text:str):
        Log.debug("[LiveScript] -> "+text)

    @staticmethod
    def write_text(row, text:str, font=fonts.MAIN_FONT, centered=True):
        SCREEN.write_text(row, text, is_system=True)

    @staticmethod
    def push_button(button:Enums.Btn):
        CENTAUR_BOARD.push_button(button)
        time.sleep(.5)

    @staticmethod
    def select_menu(name:str):

        _api._debug(f"Selecting menu '{name}'...")

        count = 15
        name = name.upper()
        while CENTAUR_BOARD.current_menu != name:
            count -= 1

            if count == 0:
                raise Exception(f'Menu "{name}" not found!')

            CENTAUR_BOARD.push_button(Enums.Btn.DOWN)
            time.sleep(.5)

        time.sleep(.5)
        CENTAUR_BOARD.push_button(Enums.Btn.TICK)
        time.sleep(.5)

    @staticmethod
    def lift_piece(source:str):
        CENTAUR_BOARD.move_piece(common.Converters.to_square_index(source), Enums.PieceAction.LIFT)

    @staticmethod
    def place_piece(target:str):
        CENTAUR_BOARD.move_piece(common.Converters.to_square_index(target), Enums.PieceAction.PLACE)
    
    @staticmethod
    def play(uci_move_string:str) -> Optional[bool]:

        _api._debug(f"Playing '{uci_move_string}'...")

        uci_moves = uci_move_string.split(' ')

        result = False

        for uci_move in uci_moves:
            if len(uci_move) != 4:
                raise Exception(f'"{uci_move}" is not a valid move!')

            CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[0:2]), Enums.PieceAction.LIFT)
            result = CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[2:4]), Enums.PieceAction.PLACE)
            time.sleep(.5)

            if not result:
                _api._debug(f"Failing to play '{uci_move}'...")
                break
            
        return result

    @staticmethod
    def take_back(count:int=1) -> bool:
        if not _api._game_engine:
            raise Exception("Game engine not started!")
        
        if not _api._game_engine:
            raise Exception("No move to take back!")
        
        result = True

        while result and count>0:

            uci_move = _api._game_engine.last_uci_move

            if not uci_move:
                raise Exception("No more move to take back!")
            
            _api._debug(f"Taking back move '{uci_move}'...")

            count -= 1

            CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[2:4]), Enums.PieceAction.LIFT)
            result = CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[0:2]), Enums.PieceAction.PLACE)

        return result

    @staticmethod
    def read_computer_move() -> str:
        if not _api._game_engine:
            raise Exception("Game engine not started!")
        
        return _api._game_engine.computer_uci_move
    
    @staticmethod
    def waitfor_screen_text(text:str, timeout:int=5, raise_exception:bool=True) -> bool:
        
        time_start = time.time()

        _api._debug(f"Waiting for text '{text}'...")

        text = text.upper()

        while text not in SCREEN.last_written_text:

            if time.time()-time_start>timeout:
                if raise_exception:
                    raise Exception(f'Timeout when waiting for text "{text}"!')
                else:
                    return False
            time.sleep(.1)

        return True
    
    @staticmethod
    def waitfor_fen_position(timeout:int=5, fen:str=chess.STARTING_FEN):

        time_start = time.time()

        _api._debug(f"Waiting for fen '{fen}'...")

        while _api.chessboard().fen() != fen:

            if time.time()-time_start>timeout:
                raise Exception(f'Timeout when waiting for fen position "{fen}"!')

            time.sleep(.1)

        time.sleep(2)
    
    @staticmethod
    def waitfor_sound(sound:Enums.Sound, timeout:int=5, raise_exception:bool=True) -> bool:
        
        time_start = time.time()

        _api._debug(f"Waiting for sound '{sound}'...")

        while sound != CENTAUR_BOARD.last_sound:

            if time.time()-time_start>timeout:
                if raise_exception:
                    raise Exception(f'Timeout when waiting for sound {sound}!')
                else:
                    return False
            time.sleep(.1)

        return True

    @staticmethod
    def waitfor_computer_move(timeout:int=15) -> str:
        if not _api._game_engine:
            raise Exception("Game engine not started!")
        
        _api._debug("Waiting for computer move...")
        
        time_start = time.time()

        while not _api._game_engine.computer_move_is_ready:

            if time.time()-time_start>timeout:
                raise Exception("Timeout when waiting for computer move!")

            time.sleep(.1)

        return _api._game_engine.computer_uci_move
    
    @staticmethod
    def chessboard() -> chess.Board:
        if not _api._game_engine:
            raise Exception("Game engine not started!")
        
        return _api._game_engine.chessboard

class _LiveScript(common.Singleton):

    _worker:Optional[threading.Thread] = None

    def __call__(self, script:str):
        try:

            if self._worker:
                self._worker.join()
                self._worker = None

            module = types.ModuleType("__LIVE_SCRIPT__")

            def _live_script_worker():

                try:
                    exec(script, module.__dict__)
                    SOCKET.send_web_message({ "popup":"Live script ended successfully!" })
                except Exception as e:
                    SOCKET.send_web_message({ "script_output":Log.last_exception() })
                    pass

            self._worker = threading.Thread(target=_live_script_worker)
            self._worker.daemon = True
            self._worker.start()

        except Exception as e:
            Log.exception(_LiveScript.execute_live_script, e)
            pass

def execute(script):
    return _LiveScript()(script)

def get():
    return _api()

def attach_game_engine(engine:GameFactory.Engine):
    _api._game_engine = engine

def detach_game_engine():
    _api._game_engine = None