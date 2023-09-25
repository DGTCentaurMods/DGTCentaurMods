from DGTCentaurMods.classes import Log, GameFactory, CentaurBoard, CentaurScreen, SocketClient
from DGTCentaurMods.lib import common
from DGTCentaurMods.consts import Enums, fonts

import types, threading, time
from typing import Optional

import chess

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()
SOCKET = SocketClient.get()

class _api():

    _game_engine:Optional[GameFactory.Engine] = None

    @staticmethod
    def write_text(row, text:str, font=fonts.MAIN_FONT, centered=True):
        SCREEN.write_text(row, text, is_system=True)

    @staticmethod
    def push_button(button:Enums.Btn):
        CENTAUR_BOARD.push_button(button)
        time.sleep(.5)

    @staticmethod
    def select_menu(name:str):
        count = 15
        name = name.upper()
        while CENTAUR_BOARD.current_menu != name:
            count -= 1

            if count == 0:
                raise Exception(f'Menu "{name}" not found!')

            CENTAUR_BOARD.push_button(Enums.Btn.DOWN)
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
    def play(uci_move:str) -> Optional[bool]:
        CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[0:2]), Enums.PieceAction.LIFT)
        result = CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[2:4]), Enums.PieceAction.PLACE)
        time.sleep(.5)
        return result

    @staticmethod
    def take_back():
        if not _api._game_engine:
            raise Exception("Game engine not started!")
        
        if not _api._game_engine:
            raise Exception("No move to take back!")
        
        uci_move = _api._game_engine.last_uci_move

        CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[2:4]), Enums.PieceAction.LIFT)
        return CENTAUR_BOARD.move_piece(common.Converters.to_square_index(uci_move[0:2]), Enums.PieceAction.PLACE)

    @staticmethod
    def read_computer_move() -> str:
        if not _api._game_engine:
            raise Exception("Game engine not started!")
        
        return _api._game_engine.computer_uci_move
    
    @staticmethod
    def waitfor_screen_text(text:str, timeout:int=5, raise_exception:bool=True) -> bool:
        
        time_start = time.time()

        Log.debug(f"Waiting for text '{text}'...")

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

        Log.debug(f"Waiting for fen '{fen}'...")

        while _api.chessboard().fen() != fen:

            if time.time()-time_start>timeout:
                raise Exception(f'Timeout when waiting for fen position "{fen}"!')

            time.sleep(.1)

        time.sleep(2)
    
    @staticmethod
    def waitfor_sound(sound:Enums.Sound, timeout:int=5, raise_exception:bool=True) -> bool:
        
        time_start = time.time()

        Log.debug(f"Waiting for sound '{sound}'...")

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
        
        Log.debug("Waiting for computer move...")
        
        time_start = time.time()

        while not _api._game_engine.computer_move_is_set:

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
                    SOCKET.send_message({ "popup":"Live script ended successfully!" })
                except:
                    SOCKET.send_message({ "script_output":Log.last_exception() })
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