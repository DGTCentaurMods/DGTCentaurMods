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

from DGTCentaurMods.classes import GameFactory, Log, CentaurBoard, CentaurScreen, SocketClient
from DGTCentaurMods.consts import Enums, consts, fonts
from DGTCentaurMods.lib import common
from DGTCentaurMods.consts import menu

from PIL import ImageFont

import chess

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

class Centaur():

    _current_row = 1

    @staticmethod
    def clear_screen():
        SCREEN.clear_area()
        Centaur._current_row = 1
    
    @staticmethod
    def print(text:str = consts.EMPTY_LINE, row:int = -1, font=fonts.MAIN_FONT):
        if row>-1:
            Centaur._current_row = row

        SCREEN.write_text(Centaur._current_row , text, font=font)
        Centaur._current_row += 1
    
    @staticmethod
    def flash(square:str):
        CENTAUR_BOARD.led(common.Converters.to_square_index(square))
    
    @staticmethod
    def light_move(uci_move:str):
        CENTAUR_BOARD.led_from_to(
            common.Converters.to_square_index(uci_move[0:2]),
            common.Converters.to_square_index(uci_move[2:4]))
    
    @staticmethod
    def lights_off():
        CENTAUR_BOARD.leds_off()
    
    @staticmethod
    def sound(sound:Enums.Sound):
        CENTAUR_BOARD.beep(sound)
    

class Plugin():

    def __init__(self, id:str):
        self._exit_requested = False
        self._id = id

        SCREEN.clear_area()

        CENTAUR_BOARD.subscribe_events(self.__key_callback, self.__field_callback)

        self._socket = SocketClient.get(on_socket_request=self._on_socket_request)

        self._initialize_web_menu()

    def _initialize_web_menu(self):
        if self._socket:
            self._socket.send_message({ 
                    "turn_caption":"Plugin "+self._id,
                    "clear_board_graphic_moves":False,
                    "loading_screen":False,
                    "evaluation_disabled":True,
                    "update_menu": menu.get(menu.Tag.ONLY_WEB, ["homescreen", "links", "settings", "system", "plugin_edit"])
                })

    def _on_socket_request(self, data, socket):
        try:

            if "web_menu" in data:
                self._initialize_web_menu()

            if "battery" in  data:
                SCREEN.set_battery_value(data["battery"])

            if "web_move" in data:

                # A move has been triggered from web UI
                self.field_callback(data["web_move"]["source"], Enums.PieceAction.LIFT, web_move=True)
                self.field_callback(data["web_move"]["target"], Enums.PieceAction.PLACE, web_move=True)

            if "web_button" in data:
                CENTAUR_BOARD.push_button(Enums.Btn(data["web_button"]))

            if "sys" in data:
                if data["sys"] == "homescreen":
                    CENTAUR_BOARD.push_button(Enums.Btn.BACK)

        except Exception as e:
            Log.exception(Plugin._on_socket_request, e)
            pass

    def __key_callback(self, key:Enums.Btn):

        if key == Enums.Btn.BACK:
            self.stop()
            return
        
        self.key_callback(key)

    def __field_callback(self,
                field_index:chess.Square,
                field_action:Enums.PieceAction,
                web_move:bool = False):

        self.field_callback(common.Converters.to_square_name(field_index), field_action, web_move)

    def _running(self):
        return not self._exit_requested

    def start(self):
        Log.info(f'Starting plugin "{self._id}"...')
        return

    def stop(self):
        Log.info(f'Stopped plugin "{self._id}"...')
        CENTAUR_BOARD.unsubscribe_events()
        self._socket.disconnect()
        self._exit_requested = True

    def key_callback(self, key:Enums.Btn):
        raise NotImplementedError("Your plugin must override key_callback!")
    
    def field_callback(self,
                square:str,
                field_action:Enums.PieceAction,
                web_move:bool):
        raise NotImplementedError("Your plugin must override key_callback!")