# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
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
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.board import board
from DGTCentaurMods.display import epaper
from DGTCentaurMods.game.classes import ChessEngine, DAL, Log
from DGTCentaurMods.game.consts import Enums, fonts, consts
from DGTCentaurMods.game.lib import common

import socketio



class _SocketClient():

    __socket = None
        
    def __init__(self, on_socket_request=None):

        try:

            self._on_socket_request = on_socket_request

            sio = socketio.Client()
            sio.connect('http://localhost')

            @sio.on('request')
            def request(data):

                if self._on_socket_request:
                    self._on_socket_request(data, self)

            self.__socket = sio

        except:
            Log.exception("_SocketClient:Unable to connect to SOCKETIO SERVER!")
            pass

    def send_message(self, message):

        try:
            if self.__socket != None:
                self.__socket.emit('message', message)

        except Exception as e:
            Log.exception(f"_SocketClient.send_message:{e}")
            pass

    def disconnect(self):
        try:
            if self.__socket != None:
                self.__socket.disconnect()

        except Exception as e:
            Log.exception(f"_SocketClient.disconnect:{e}")
            pass


def get(on_socket_request):
    return _SocketClient(on_socket_request)