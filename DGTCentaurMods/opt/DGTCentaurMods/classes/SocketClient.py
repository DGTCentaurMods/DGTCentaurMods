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
from DGTCentaurMods.lib import common

import socketio

class _SocketClient(common.Singleton):

    _socket = None
    _on_socket_request = None

    _callbacks_queue = []

    _initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized
        
    def initialize(self, on_socket_request:callable = None, uri:str = None):

        try:
            self._initialized = True

            if on_socket_request:
                self._callbacks_queue.append(self._on_socket_request)
                self._on_socket_request = on_socket_request

            # If the one socket already exists, we use the same one
            if self._socket == None:

                uri = uri or 'http://localhost'

                Log.debug(f"-> Connecting to {uri}...", console=True)

                sio = socketio.Client()
                sio.connect(uri)

                '''
                @sio.event
                def connect():
                    Log.debug(f"-> Connected to {uri}...", console=True)

                @sio.event
                def disconnect():
                    Log.debug(f"-> Disconnected from {uri}...", console=True)
                '''

                @sio.on('request')
                def request(data):
                    if self._on_socket_request:
                        self._on_socket_request(data, self)

                self._socket = sio

        except:
            Log.exception(_SocketClient.__init__, "Unable to connect to SOCKETIO SERVER!")
            pass

        return self

    def send_request(self, request):
        try:
            if self._socket != None:
                self._socket.emit('request', request)

        except:
            Log.info("Socket disconnected...")
            pass

    def send_web_message(self, message):
        try:
            if self._socket != None:
                self._socket.emit('web_message', message)

        except Exception as e:
            Log.info("Socket disconnected...")
            pass

    def disconnect(self):

        try:
            if self._socket != None:

                if len(self._callbacks_queue):
                    # We don't disconnect the socket while we have
                    # one available callback
                    self._on_socket_request = self._callbacks_queue.pop()
                else:
                    self._socket.disconnect()

        except Exception as e:
            Log.exception(_SocketClient.disconnect, e)
            pass

def connect_local_server() -> _SocketClient:
    return _SocketClient().initialize()

def get() -> _SocketClient:
    return _SocketClient()