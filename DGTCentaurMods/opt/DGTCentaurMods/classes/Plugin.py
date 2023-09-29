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

from __future__ import annotations

from DGTCentaurMods.classes import GameFactory, Log, ChessEngine, CentaurBoard, CentaurScreen, SocketClient
from DGTCentaurMods.classes.CentaurConfig import CentaurConfig
from DGTCentaurMods.consts import Enums, consts, fonts
from DGTCentaurMods.lib import common, sys_requests
from DGTCentaurMods.consts import menu

from typing import Optional, Callable, Tuple, List

from chess.engine import PovScore, Limit
import chess

TAnalyseResult = ChessEngine.TAnalyseResult
TPlayResult = ChessEngine.TPlayResult

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()
SOCKET = SocketClient.connect_local_server()

class Centaur():

    _current_row:int = 1
    _plugin:Plugin = None
    _chess_engine:Optional[ChessEngine.ChessEngineWrapper] = None

    @staticmethod
    def _attach_plugin(plugin):
        Centaur._plugin = plugin

    @staticmethod
    def _detach_plugin():
        Centaur._plugin = None

    @staticmethod
    def delayed_call(call:callable, delay:int):
        common.delayed_call(call, delay)

    @staticmethod
    def configuration() -> CentaurConfig:
        return CentaurConfig

    @staticmethod
    def send_external_request(request:dict):
        request["_plugin"] = Centaur._plugin.__class__.__name__
        SOCKET.send_web_message({ consts.EXTERNAL_REQUEST: request })

    @staticmethod
    def push_button(button:Enums.Btn):
        CENTAUR_BOARD.push_button(button)
   
    @staticmethod
    def clear_screen():
        SCREEN.clear_area()
        Centaur._current_row = 1
    
    @staticmethod
    def print_button_label(button:Enums.Btn, x:int, row:float = -1, text:str=""):
        if row>-1:
            Centaur._current_row = row
    
        SCREEN.draw_button_label(button, text, Centaur._current_row, x)

        Centaur._current_row += 1

    @staticmethod
    def messagebox(text_lines:Tuple[str,...], row:float=8, tick_button:bool=False):
        SCREEN.draw_messagebox(text_lines, row=row, tick_button=tick_button)

    @staticmethod
    def print(text:str = consts.EMPTY_LINE, row:float = -1, font=fonts.MAIN_FONT):
        if row>-1:
            Centaur._current_row = row

        SCREEN.write_text(Centaur._current_row , text, font=font)
        Centaur._current_row += 1
    
    @staticmethod
    def flash(square:str):
        CENTAUR_BOARD.led(common.Converters.to_square_index(square))
    
    @staticmethod
    def light_move(uci_move:str, web:bool=True):
        CENTAUR_BOARD.led_from_to(
            common.Converters.to_square_index(uci_move[0:2]),
            common.Converters.to_square_index(uci_move[2:4]))
        
        if web:
            SOCKET.send_web_message({ 
                "tip_uci_move":uci_move
            })

    @staticmethod
    def light_moves(uci_moves:Tuple[str], web:bool=True):

        squares = []
        moves = []

        for uci_move in uci_moves:

            moves.append(uci_move[0:4])

            squares.append(common.Converters.to_square_index(uci_move[0:2]))
            squares.append(common.Converters.to_square_index(uci_move[2:4]))

        CENTAUR_BOARD.led_array(squares)
        
        if web:
            SOCKET.send_web_message({ 
                "tip_uci_moves":moves
            })
    
    @staticmethod
    def lights_off():
        CENTAUR_BOARD.leds_off()
    
    @staticmethod
    def sound(sound:Enums.Sound, override:Optional[Enums.Sound]=None):
        CENTAUR_BOARD.beep(sound, override)

    @staticmethod
    def header(text:str,web_text:str=None):
        SCREEN.write_text(1, text, font=fonts.MEDIUM_MAIN_FONT)

        SocketClient.connect_local_server().send_web_message({"turn_caption":web_text or text})

    @staticmethod
    def start_game(
                event:str="",
                site:str="",
                white:str="",
                black:str="",
                flags:Enums.BoardOption=Enums.BoardOption.CAN_FORCE_MOVES | Enums.BoardOption.CAN_UNDO_MOVES):

        if Centaur._plugin:
            Centaur._plugin._start_game(event,site,white,black,flags, chess_engine=Centaur._chess_engine)

    @staticmethod
    def play_computer_move(uci_move:str):
        if Centaur._plugin:
            Centaur._plugin._play_computer_move(uci_move)

    @staticmethod
    def computer_move_is_ready() -> bool:
        if Centaur._plugin:
            return Centaur._plugin._computer_move_is_ready()

    @staticmethod
    def hint():
        if Centaur._plugin:
            Centaur._plugin._hint()

    @staticmethod
    def pause_plugin():
        if Centaur._plugin:
            Centaur._plugin._started = False

    @staticmethod
    def set_chess_engine(engine_name):
        Centaur._chess_engine = ChessEngine.get(f"{consts.ENGINES_DIRECTORY}/{engine_name}")
    
    @staticmethod
    def configure_chess_engine(options:dict):
        if Centaur._chess_engine:
            Centaur._chess_engine.configure(options)

    @staticmethod
    def request_chess_engine_move(engine_callback:Callable[[], ChessEngine.TPlayResult], time:int=5):
        if Centaur._chess_engine and Centaur._plugin:

            Centaur._chess_engine.play(
                Centaur._plugin.game_engine.chessboard,
                limit=Limit(time=time),

                on_move_done = engine_callback)
                
    @staticmethod
    def request_chess_engine_evaluation(engine_callback:Callable[[PovScore, List[chess.Move]]], time:int=2, multipv:int=1):
        if Centaur._chess_engine and Centaur._plugin:

            Centaur._chess_engine.analyse(
                Centaur._plugin.game_engine.chessboard,
                multipv=multipv,
                limit=Limit(time=time),
    
                on_analyse_done = engine_callback)
            
    '''
    @staticmethod
    def launch_chess_engine_analysis(
        on_analysis:Callable[[PovScore, List[chess.Move]], bool], 
        on_analysis_ended:Callable[[int], None],
        engine_name:Optional[str]=None,
        depth:int=5, time:int=2, multipv:int=3):

        if Centaur._chess_engine and Centaur._plugin:
            Centaur._chess_engine.launch_analysis(

                Centaur._plugin.game_engine.chessboard,
                limit = Limit(time=time, depth=depth),

                multipv = multipv,

                engine_name = engine_name,

                on_analysis = on_analysis,
                on_analysis_ended = on_analysis_ended)
    '''
            
    @staticmethod
    def reverse_board(value:Optional[bool]=True):
        SCREEN.set_reversed(value)


class Plugin():

    _game_engine:Optional[GameFactory.Engine] = None

    @property
    def game_engine(self) -> Optional[GameFactory.Engine]:
        return self._game_engine

    def __init__(self, id:str):
        self._exit_requested = False
        self._id = id
        
        self._started:bool = False

        Centaur._attach_plugin(self)

        SCREEN.clear_area()

        CENTAUR_BOARD.subscribe_events(self.__key_callback, self.__field_callback)

        SOCKET.initialize(on_socket_request=self._on_socket_request)

        self._initialize_web_menu()

    def _initialize_web_menu(self):

        SOCKET.send_web_message({ 
                "turn_caption":"Plugin "+common.camel_case_to_snake_case(self._id),
                "plugin":self._id,
                "clear_board_graphic_moves":True,
                "loading_screen":False,
                "update_menu": menu.get(menu.Tag.ONLY_WEB, ["homescreen", "links", "settings", "system", "plugin_edit"])
            })

    def _on_socket_request(self, data, socket):
        try:
            # Common sys requests handling
            sys_requests.handle_socket_requests(data)

            if "web_menu" in data:
                self._initialize_web_menu()
                del data["web_menu"]

            if "web_move" in data:
                # A move has been triggered from web UI
                CENTAUR_BOARD.move_piece(common.Converters.to_square_index(data["web_move"].get("source", None)), Enums.PieceAction.LIFT)
                CENTAUR_BOARD.move_piece(common.Converters.to_square_index(data["web_move"].get("target", None)), Enums.PieceAction.PLACE)
                del data["web_move"]

            if "web_button" in data:
                CENTAUR_BOARD.push_button(Enums.Btn(data["web_button"]))
                del data["web_button"]

            # Plugin needs to be started to 
            # receive socket requests.
            if self._started:

                if consts.EXTERNAL_REQUEST in data:
                    # We only accept requests that come from the same plugin
                    if data[consts.EXTERNAL_REQUEST].get("_plugin", None) == Centaur._plugin.__class__.__name__:
                        self.on_socket_request(data)
                else:
                    pass
                    self.on_socket_request(data)

        except:
            socket.send_web_message({ "script_output":Log.last_exception() })
            self.stop()

    def __key_callback(self, key:Enums.Btn):
        try:
            if key == Enums.Btn.BACK:

                if self._game_engine:
                    self._game_engine.end()
                else:
                    self.stop()

                # The key has been handled
                return True
            
            if not self._started:
                self._started = self.on_start_callback(key)
            
            if not self._started:
                return False

            return self.key_callback(key)

        except:
            SOCKET.send_web_message({ "script_output":Log.last_exception() })
            self.stop()

    def __field_callback(self,
                field_index:chess.Square,
                field_action:Enums.PieceAction,
                web_move:bool = False):
        try:
            if self._started:
                self.field_callback(common.Converters.to_square_name(field_index), field_action, web_move)
        
        except:
            SOCKET.send_web_message({ "script_output":Log.last_exception() })
            self.stop()

    def __event_callback(self, event:Enums.Event, outcome:Optional[chess.Outcome]):
        try:
            if self._started:
                self.event_callback(event, outcome)

        except:
            SOCKET.send_web_message({ "script_output":Log.last_exception() })
            self.stop()
    
    def __move_callback(self, uci_move:str, san_move:str, color:chess.Color, field_index:chess.Square):
        try:
            if self._started:
                return self.move_callback(uci_move, san_move, color, field_index)
        
        except:
            SOCKET.send_web_message({ "script_output":Log.last_exception() })
            self.stop()
        
        return False
    
    def __undo_callback(self, uci_move:str, san_move:str, field_index:chess.Square):
        try:
            if self._started:
                return self.undo_callback(uci_move, san_move, field_index)
        
        except:
            SOCKET.send_web_message({ "script_output":Log.last_exception() })
            self.stop()
        
        return False
    
    def __socket_callback(self, data:dict, _):

        try:
            if self._started and len(data.keys())>0:
                return self.on_socket_request(data)
        
        except:
            SOCKET.send_web_message({ "script_output":Log.last_exception() })
            self.stop()
        
        return False
    
    def _running(self):
        return not self._exit_requested
    
    # Invoked from Centaur API
    def _hint(self):
        if not self._game_engine:
            raise Exception("Game engine not started!")
        
        self._game_engine.flash_hint()

    # Invoked from Centaur API
    def _play_computer_move(self, uci_move:str):
        if not self._game_engine:
            raise Exception("Game engine not started!")
        
        self._game_engine.set_computer_move(uci_move)

    # Invoked from Centaur API
    def _computer_move_is_ready(self) -> bool:
        if not self._game_engine:
            raise Exception("Game engine not started!")
        
        return self._game_engine.computer_move_is_ready
        
    # Invoked from Centaur API
    def _start_game(self, event:str, site:str, white:str, black:str, flags:Enums.BoardOption, chess_engine: Optional[ChessEngine.ChessEngineWrapper] = None):
        
        if self._game_engine == None:
            self._game_engine = GameFactory.Engine(
            
                undo_callback = self.__undo_callback,
                event_callback = self.__event_callback,
                key_callback = self.__key_callback,
                move_callback = self.__move_callback,
                socket_callback = self.__socket_callback,

                flags = flags,

                chess_engine = chess_engine,
                
                game_informations = {
                    "event" : event,
                    "site"  : site,
                    "round" : "",
                    "white" : white,
                    "black" : black,
                })

            self._game_engine.start()

    @property
    def chessboard(self):
        if not self._game_engine:
            raise Exception("Game engine not started!")
        
        return self._game_engine.chessboard
    
    @property
    def started(self):
        return self._started

    def start(self):
        Log.info(f'Starting plugin "{self._id}"...')
        if not self.splash_screen():
            self._started = True
            self.on_start_callback()

    def stop(self):
        Log.info(f'Stopping plugin "{self._id}"...')

        if self._game_engine:
            self._game_engine.stop()
            self._game_engine = None

        if Centaur._chess_engine:
            Centaur._chess_engine.quit()

        Centaur._chess_engine = None

        CENTAUR_BOARD.unsubscribe_events()

        Centaur._detach_plugin()

        SOCKET.disconnect()
        self._exit_requested = True

    def key_callback(self, key:Enums.Btn):
        raise NotImplementedError("Your plugin must override key_callback!")
    
    def field_callback(self,
                square:str,
                field_action:Enums.PieceAction,
                web_move:bool):
        return
    
    def event_callback(self, event:Enums.Event, outcome:Optional[chess.Outcome]):
        return
    
    def undo_callback(self, uci_move:str, san_move:str, field_index:chess.Square):
        return
    
    def move_callback(self, uci_move:str, san_move:str, color:chess.Color, field_index:chess.Square) -> bool:
        return True
    
    def on_start_callback(self, key:Enums.Btn) -> bool:
        return True
    
    def on_socket_request(self, data:dict):
        return

    def splash_screen(self) -> bool:
        self._started = True
        return False