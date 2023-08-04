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

from DGTCentaurMods.game.classes import Log, SocketClient, CentaurScreen, CentaurBoard
from DGTCentaurMods.game.consts import consts
from DGTCentaurMods.game.lib import common

from pathlib import Path

import time, sys, os, configparser, re, copy

import importlib, shlex

CENTAUR_BOARD = CentaurBoard.get()
SCREEN = CentaurScreen.get()

# Menu items
# Proto version, shared between web & ePaper
MENU_ITEMS = [

    {   "id":"play", 
        "label":"Play", 
        "items": [
            {"label": "Resume last game", 
             "action": { "type": "socket_execute", "value": "uci_resume.py"} },
            {"label": "Play 1 vs 1", 
             "action":{ "type": "socket_execute", "value": "1vs1_module.py"} },
        ],
        "disabled": True }, 
    
    { "label":"Links", "only_web":True, "items": [
            {"label": "Open Lichess position analysis", 
             "action" :{ "type": "js", "value": '() => window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")' }},
            {"label": "Open Lichess PGN import page", 
             "action":{ "type": "js", "value": '() => window.open("https://lichess.org/paste", "_blank")' }},
            {"label": "View current PGN", 
             "action":{ "type": "js", "value": '() => me.viewCurrentPGN()' }},
        ],
        "disabled": False }, 
    
    { "label":"Display settings", "only_web":True, "action":{"type": "js_variable", "value": "displaySettings"}, "disabled": False }, 
    
    { "label":"Previous games", "only_web":True, "items": [], "action":{ "type": "socket_data", "value": "previous_games"}, "disabled": False }, 
    
    { "label":"System", "items": [
            { "label": "Power off board",
              "action":{ "type": "socket_sys", "message": "A shutdown request has been sent to the board!", "value": "shutdown"}
            },
            { "label": "Reboot board",
              "action":{ "type": "socket_sys", "message": "A reboot request has been sent to the board!", "value": "reboot"}
            },
            { "label": "Restart service",
              "action":{ "type": "socket_sys", "message": "A restart request has been sent to the board!", "value": "restart_service"}
            },
            { "type": "divider" },
            { "label": "Last log events",
              "action":{ "type": "socket_sys", "message": None, "value": "log_events"}
            },
        ],
        "disabled": False }
    ]



class Menu:

    _browser_connected = False

    def __init__(self):

        SCREEN.write_text(3,"Welcome!")

        def _on_socket_request(data, socket):

            #Log.debug(data)
            try:
            
                #response = {}

                if "web_menu" in data:

                    self.initialize_web_menu()

                if "pong" in data:
                    # Browser is connected (server ping)
                    self._browser_connected = True
                    #socket.send_message(response)

                if "execute" in data:

                    command = data["execute"]

                    Log.debug(command)

                    match = re.search('1vs1_module|uci_resume|uci_module|famous_module', command)

                    if match != None:

                        script = match.group()

                        self.start_child_module()

                        module = importlib.import_module(name=script, package="{consts.MAIN_ID}.game")
                   
                        args = shlex.split(command)

                        # We remove the script name
                        args.pop(0)

                        if (len(args)):
                            module.main(*args)
                        else:
                            module.main()

                        del module

                        #importlib.invalidate_caches()
                        self.end_child_module()

            except Exception as e:
                Log.exception(_on_socket_request, e)
                pass

        self._socket = SocketClient.get(on_socket_request=_on_socket_request)

        self._socket.send_message({ "ping":True, "enable_menu":"play", "loading_screen":False, "popup":"The service is up and running!" })

        CENTAUR_BOARD.subscribe_events(self._key_callback, self._field_callback)

    def _key_callback(self, key_index):
        print(key_index)
    
    def _field_callback(self, field_index):
        return

    # Add engines and famous PGNs to proto menu
    def build_menu_items(self):

        result = copy.deepcopy(MENU_ITEMS)
        
        play_item = next(filter(lambda item:item["id"] == "play", result))

        ENGINE_PATH = consts.OPT_DIRECTORY+"/engines"
        PGNS_PATH = consts.OPT_DIRECTORY+"/game/famous_pgns"

        def get_sections(uci_file):
            parser = configparser.ConfigParser()
            parser.read(uci_file)

            return list(map(lambda section:section, parser.sections()))

        # We read the available engines + their options
        engines = list(map(lambda f:{"id":Path(f.name).stem, "options":get_sections(f.path)}, 
                           filter(lambda f: f.name.endswith(".uci"), os.scandir(ENGINE_PATH))))
        
        # Stockfish has no configuration file (we might create one...)
        engines.append({ "id":"stockfish", "options":["1350","1400","1500","1600","1700","1800","2000","2200","2400","2600","2850"]})

        famous_pgns = list(map(lambda f:Path(f.name).stem, 
                           filter(lambda f: f.name.endswith(".pgn"), os.scandir(PGNS_PATH))))


        # Famous PGN menu item
        play_item["items"].append({ "label": "Play famous games", "type": "subitem", 
                                   "items":list(map(lambda pgn: { "label": "⭐ "+pgn.capitalize(), "action": { "type": "socket_execute", "value": f'famous_module.py "{pgn}.pgn"' }},famous_pgns)) })

        # Engines menu items
        for engine in engines:

            engine_menu = { "label": "Play "+engine["id"].capitalize(), "type": "subitem", "items":[] }

            play_item["items"].append(engine_menu)
            
            for option in engine["options"]:
                    
                engine_menu["items"].append({
                        "label": "⭐ "+option.capitalize(),
                        "action": { "type": "socket_execute", "dialogbox": "color", "value": "uci_module.py {value} "+engine["id"]+' "'+option+'"' } })

        return result


    def initialize_web_menu(self, message={}):

        message["enable_menu"] = "play"

        message["update_menu"] = self.build_menu_items()
        
        self._socket.send_message(message)

    def start_child_module(self):

        if self._socket != None:
            self._socket.send_message({ "disable_menu":"play", "loading_screen":True })

    def end_child_module(self):

        if self._socket != None:
            self._socket.send_message({ "enable_menu":"play", "popup":"The current game has been paused!" })

    def disconnect(self):

        if self._socket != None:
            self._socket.disconnect()

    def browser_connected(self):
        return self._browser_connected


Menu()

while True:
    time.sleep(.5)
    
#subprocess.call([sys.executable, consts.OPT_DIRECTORY + "/game/menu.legacy.py"])