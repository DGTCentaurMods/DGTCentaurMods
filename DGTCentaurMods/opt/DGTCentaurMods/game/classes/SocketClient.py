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

from DGTCentaurMods.game.classes import Log
from DGTCentaurMods.game.lib import common

import socketio

class _SocketClient(common.Singleton):

    __socket = None
    _on_socket_request = None

    __callbacks_queue = []
        
    def initialize(self, on_socket_request):

        try:
            self.__callbacks_queue.append(self._on_socket_request)
            self._on_socket_request = on_socket_request

            # If the one socket already exists, we use the same one
            if self.__socket == None:

                sio = socketio.Client()
                sio.connect('http://localhost')

                Log.debug(f"{str(_SocketClient.__init__)}[{sio.get_sid()}]")

                @sio.on('request')
                def request(data):

                    if self._on_socket_request:
                        self._on_socket_request(data, self)

                self.__socket = sio

            return self

        except:
            Log.exception(_SocketClient.__init__, "Unable to connect to SOCKETIO SERVER!")
            pass

    def send_message(self, message):

        try:
            if self.__socket != None:
                self.__socket.emit('message', message)

        except Exception as e:
            Log.exception(_SocketClient.send_message, e)
            pass

    def disconnect(self):

        try:
            if self.__socket != None:

                self._on_socket_request = self.__callbacks_queue.pop()

                if self._on_socket_request == None:
                    Log.debug(f"{str(_SocketClient.disconnect)}[{self.__socket.get_sid()}]")
                    self.__socket.disconnect()

                else:
                    # We don't disconnect the socket since we have
                    # One available callback
                    pass

        except Exception as e:
            Log.exception(_SocketClient.disconnect, e)
            pass


def get(on_socket_request):
    return _SocketClient().initialize(on_socket_request)