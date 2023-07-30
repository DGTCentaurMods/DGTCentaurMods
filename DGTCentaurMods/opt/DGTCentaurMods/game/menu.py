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

from DGTCentaurMods.game.classes import Log, SocketClient
from DGTCentaurMods.game.consts import consts
from DGTCentaurMods.game.lib import common
from DGTCentaurMods.display import epd2in9d

from pathlib import Path

import time, sys, os, configparser
import subprocess

class Menu:

    _module_is_running = False
    _browser_connected = False

    def __init__(self):

        def _on_socket_request(data, socket):

            # If a module is running, we ignore the socket requests
            if (self._module_is_running):
                return

            try:
            
                #response = {}

                if "web_menu" in data:
                    self.initialize_web_menu()

                if "pong" in data:
                    # Browser is connected (server ping)
                    self._browser_connected = True
                    #socket.send_message(response)

                if "menu" in data:

                    GAME_PATH = consts.OPT_DIRECTORY + "/game/"
                    UCI_MODULE_PATH = GAME_PATH + "uci_module.py"

                    action = data["menu"]

                    Log.debug(action)

                    if action == "1vs1_module":

                        self.start_child_module()
                   
                        subprocess.call([sys.executable, f"{GAME_PATH}{action}.py"])
                        
                        self.end_child_module()

                    if action == "uci_resume":
                        self.start_child_module()

                        last_uci = common.get_last_uci_command()
                        subprocess.call([sys.executable, UCI_MODULE_PATH]+last_uci.split())
                        
                        self.end_child_module()

                    if action[:10] == "uci_module":
                        self.start_child_module()

                        args = list(map(lambda arg:arg.replace('___', ' '), action.split()))
                        args.pop(0)
                        subprocess.call([sys.executable, UCI_MODULE_PATH]+args)
                        
                        self.end_child_module()

            except Exception as e:
                Log.exception(f"_on_socket_request:{e}")
                pass

        self._socket = SocketClient.get(on_socket_request=_on_socket_request)

        self._socket.send_message({ "ping":True, "popup":"The service is up and running!" })

    def clear_screen(self):
        epd = epd2in9d.EPD()
        epd.init()
        epd.Clear(0xff)

    def initialize_web_menu(self, message={}):
        message["enable_menu"] = "play"

        ENGINE_PATH = consts.OPT_DIRECTORY+"/engines"

        def get_sections(uci_file):
            parser = configparser.ConfigParser()
            parser.read(uci_file)
            # We replace section name spaces by '___' to avoid string to be later split
            return list(map(lambda section:section.replace(' ','___'), parser.sections()))

        # We read the available engines + their options
        engines = list(map(lambda f:{"id":Path(f.name).stem, "options":get_sections(f.path)}, 
                           filter(lambda f: f.name.endswith(".uci"), os.scandir(ENGINE_PATH))))
        
        # Stockfish has no configuration file (we might create one...)
        engines.append({ "id":"stockfish", "options":["1350","1400","1500","1600","1700","1800","2000","2200","2400","2600","2850"]})

        # ...and we send back them to the browser
        message["update_menu"] = { "id":"play", "engines":engines }

        self._socket.send_message(message)

    def start_child_module(self):
        self._module_is_running = True
        self._socket.send_message({ "disable_menu":"play", "loading_screen":True, "popup":"The board is being initialized..." })

    def end_child_module(self):
        self._module_is_running = False
        self._socket.send_message({ "enable_menu":"play", "popup":"The current game has been paused!" })


    def disconnect(self):
        self._socket.disconnect()

    def browser_connected(self):
        return self._browser_connected


menu = Menu()
menu.clear_screen()

time.sleep(1)

if menu.browser_connected():
    Log.info("At least one browser is connected, legacy menu is disabled.")
    menu.initialize_web_menu({ "popup":"Legacy menu has been disabled!" })
    while True:
        time.sleep(.5)
else:
    menu.disconnect()

    del menu

    subprocess.call([sys.executable, consts.OPT_DIRECTORY + "/game/menu.legacy.py"])