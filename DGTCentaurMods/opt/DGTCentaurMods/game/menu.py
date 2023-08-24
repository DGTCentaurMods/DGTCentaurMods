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
from DGTCentaurMods.game.consts import consts, fonts, Enums
from DGTCentaurMods.game.lib import common

from pathlib import Path

import time, sys, os, configparser, re, copy

import importlib, shlex

CENTAUR_BOARD = CentaurBoard.get()
SCREEN = CentaurScreen.get()

CURRENT_INDEX = "current_index"
CURRENT_NODE = "current_node"
CURRENT_VALUE = "current_value"
NODE_INDEXES = "node_indexes"
ITEMS = "items"
NODES = "nodes"
ACTION = "action"
LABEL = "label"
SHORT_LABEL = "short_label"
VALUE = "value"
TYPE = "type"

# Menu items
# Proto version, shared between web & ePaper
MENU_ITEMS = [

    {   "id":"play", 
        LABEL:"Play", 
        ITEMS: [
            {LABEL: "Resume last game", SHORT_LABEL: "Resume",
             ACTION: { TYPE: "socket_execute", VALUE: "uci_resume.py"} },
            {LABEL: "Play 1 vs 1", 
             ACTION:{ TYPE: "socket_execute", VALUE: "1vs1_module.py"} },
        ] }, 
    
    { LABEL:"Links", "only_web":True, ITEMS: [
            {LABEL: "Open Lichess position analysis", 
             ACTION :{ TYPE: "js", VALUE: '() => window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")' }},
            {LABEL: "Open Lichess PGN import page", 
             ACTION:{ TYPE: "js", VALUE: '() => window.open("https://lichess.org/paste", "_blank")' }},
            {LABEL: "View current PGN", 
             ACTION:{ TYPE: "js", VALUE: '() => me.viewCurrentPGN()' }},
        ]}, 
    
    { LABEL:"Settings", "only_web":True, ITEMS: [
        { LABEL:"🌈 Web display", "only_web":True, ITEMS: [], TYPE: "subitem", ACTION:{TYPE: "js_variable", VALUE: "displaySettings"} },
        { LABEL:"🎵 Board sounds", "only_web":True, ACTION:{ TYPE: "socket_data", VALUE: "sounds_settings"}}, 
    ]},
    
    { LABEL:"Previous games", "only_web":True, ACTION:{ TYPE: "socket_data", VALUE: "previous_games"} }, 
    
    {   "id":"system", 
        LABEL:"System", ITEMS: [
            { LABEL: "Power off board", SHORT_LABEL: "Power off",
              ACTION:{ TYPE: "socket_sys", "message": "A shutdown request has been sent to the board!", VALUE: "shutdown"}
            },
            { LABEL: "Reboot board", SHORT_LABEL: "Reboot",
              ACTION:{ TYPE: "socket_sys", "message": "A reboot request has been sent to the board!", VALUE: "reboot"}
            },
            { LABEL: "⚡ Restart service", "only_web":True,
              ACTION:{ TYPE: "socket_sys", "message": "A restart request has been sent to the board!", VALUE: "restart_service"}
            },
            { TYPE: "divider", "only_web":True },
            { LABEL: "📋 Last log events", "only_web":True,
              ACTION:{ TYPE: "socket_sys", "message": None, VALUE: "log_events"}
            },
            { TYPE: "divider", "only_web":True },

            { "id":"uci", LABEL:"Edit engines UCI", TYPE: "subitem", ITEMS: [], "only_web":True }

        ] },

    { LABEL:"Launch Centaur", SHORT_LABEL:"Centaur", ACTION:{ TYPE: "socket_sys", VALUE: "centaur"} },
    { LABEL:"WIFI", "only_board":True, ACTION:{ TYPE: "socket_execute", VALUE: "wifi_module"} },
]



class Menu:

    _browser_connected = False

    def home_screen(self):

        CENTAUR_BOARD.leds_off()

        self.draw_menu(True)
        #SCREEN.save_screen()

    def draw_menu(self, clear_area=False):

        # TODO to be optimized...

        is_root = len(self._menu[NODES]) == 0

        current_row = 10 if is_root else 2
        current_index = 0

        if clear_area:
            SCREEN.clear_area()

        SCREEN.write_text(current_row-.8, "choose an item", font=fonts.FONT_Typewriter_small)

        if is_root:
            SCREEN.draw_fen(common.get_Centaur_FEN())

        current_items = self._menu[CURRENT_NODE]+([{LABEL:""}]*10)

        current_item_row = current_row

        # We draw all the visible items
        for item in current_items:

            if "only_web" in item and item["only_web"] == True:
                continue

            SCREEN.write_text(current_row, item[SHORT_LABEL if SHORT_LABEL in item else LABEL])
            
            # Current selected item?
            if current_index == self._menu[CURRENT_INDEX]:
                current_item_row = current_row

            current_index = current_index +1
            current_row = current_row +1

            # Out of the screen?
            if current_row == 20:
                break

        # Then we draw the selected item
        y = current_item_row * CentaurScreen.ROW_HEIGHT
        SCREEN.draw_rectangle(0,y,CentaurScreen.SCREEN_WIDTH -1,y+CentaurScreen.ROW_HEIGHT, outline=0)
        

    def __init__(self):

        def _on_socket_request(data, socket):

            #Log.debug(data)
            try:
            
                #response = {}

                if "standby" in data:
                    if data["standby"]:
                        SCREEN.home_screen("Paused!")
                        #SCREEN.pause()
                    else:
                        #SCREEN.unpause()
                        self.draw_menu(True)

                if "battery" in  data:
                    SCREEN.set_battery_value(data["battery"])

                if "web_menu" in data:

                    self.initialize_web_menu()

                if "pong" in data:
                    # Browser is connected (server ping)
                    self._browser_connected = True
                    #socket.send_message(response)

                if "sys" in data:
                   
                    command = data["sys"]

                    Log.debug(command)

                    # The system actions are executed on server side
                    # We only handle the UI here (as the browser does)

                    if command=="reboot":
                        SCREEN.home_screen("Rebooting!")
                    
                    if command=="shutdown":
                        SCREEN.home_screen("Bye!")

                    if command=="restart_service":
                        SCREEN.home_screen("Reloading!")

                    if command=="centaur":
                        SCREEN.home_screen("Loading Centaur!")
                        CENTAUR_BOARD.pause_events()
                    

                if "execute" in data:

                    command = data["execute"]

                    Log.debug(command)

                    match = re.search('1vs1_module|uci_resume|uci_module|famous_module|wifi_module', command)

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

        self._socket.send_message({ "ping":True, "loading_screen":False, "popup":"The service is up and running!" })

        self._menu = {
            CURRENT_INDEX: 0,
            NODES: [],
            NODE_INDEXES: [],
            ITEMS: list(filter(lambda item:"only_web" not in item or item["only_web"] == False, self._build_menu_items()))
        }

        self._menu[CURRENT_NODE] = self._menu[ITEMS]

        self.home_screen()

        CENTAUR_BOARD.subscribe_events(self._key_callback, None, self._socket)

    def _key_callback(self, key_index):
        #print(key_index)

        #SCREEN.restore_screen()

        clear_area = False

        m = self._menu

        node = m[CURRENT_NODE]
        index = m[CURRENT_INDEX]

        if key_index == Enums.Btn.UP:
            if index>0:
                m[CURRENT_INDEX] = index-1
            else:
                m[CURRENT_INDEX] = len(node)-1

        if key_index == Enums.Btn.DOWN:
            if index<len(node)-1:
                m[CURRENT_INDEX] = index+1
            else:
                m[CURRENT_INDEX] = 0

        if key_index == Enums.Btn.TICK:

            if ITEMS in node[index]:
                m[CURRENT_NODE] = node[index][ITEMS]
                m[CURRENT_INDEX] = 0
                m[NODES].append(node)
                m[NODE_INDEXES].append(index)

            else:

                if ACTION in node[index] and VALUE in node[index][ACTION]:

                    value = node[index][ACTION][VALUE]
                    item_type = node[index][ACTION][TYPE]

                    if item_type == 'color':

                        value = m[CURRENT_VALUE].replace("{value}", value)

                        self._socket.send_request({'execute':value})

                    if item_type == 'socket_sys':
                        # The server will excute the command
                        self._socket.send_request({'sys':value})

                    if item_type == 'socket_execute':

                        if "dialogbox" in node[index][ACTION]:

                            # TODO align the design with the generic JS version
                            m[CURRENT_NODE] = [
                                { LABEL: "Play white",
                                ACTION:{ TYPE: "color", VALUE: "white"}
                                },
                                { LABEL: "Play black",
                                ACTION:{ TYPE: "color", VALUE: "black"}
                                },
                            ]
                            m[CURRENT_INDEX] = 0
                            m[NODES].append(node)

                            m[NODE_INDEXES].append(index)

                            m[CURRENT_VALUE] = value

                        else:
                            self._socket.send_request({'execute':value})

        if key_index == Enums.Btn.BACK:
            nodes = m[NODES]
            if len(nodes) >0:

                clear_area = True

                m[CURRENT_NODE] = nodes.pop()
                m[CURRENT_INDEX] = m[NODE_INDEXES].pop()


        self.draw_menu(clear_area)


    # Add engines and famous PGNs to proto menu
    def _build_menu_items(self):

        result = copy.deepcopy(MENU_ITEMS)
        
        play_item = next(filter(lambda item:"id" in item and item["id"] == "play", result))
        sys_item = next(filter(lambda item:"id" in item and item["id"] == "system", result))
        uci_item = next(filter(lambda item:"id" in item and item["id"] == "uci", sys_item[ITEMS]))

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
        play_item[ITEMS].append({ LABEL: "Play famous games", SHORT_LABEL: "Famous games", TYPE: "subitem", 
                                   ITEMS:list(map(lambda pgn: { LABEL: "⭐ "+pgn.capitalize(), SHORT_LABEL:pgn.capitalize(), ACTION: { TYPE: "socket_execute", VALUE: f'famous_module.py "{pgn}.pgn"' }},famous_pgns)) })

        # Engines menu items
        for engine in engines:

            engine_menu = { LABEL: "Play "+engine["id"].capitalize(), SHORT_LABEL: engine["id"].capitalize(), TYPE: "subitem", ITEMS:[] }

            play_item[ITEMS].append(engine_menu)
            
            for option in engine["options"]:
                    
                engine_menu[ITEMS].append({
                        LABEL: "⭐ "+option.capitalize(), SHORT_LABEL:option.capitalize(),
                        ACTION: { TYPE: "socket_execute", "dialogbox": "color", VALUE: "uci_module.py {value} "+engine["id"]+' "'+option+'"' } })
                

        # UCI editor menu items
        for engine in engines:

            if os.path.exists(f"{consts.OPT_DIRECTORY}/engines/{engine['id']}.uci"):

                editor_menu = { LABEL: "Edit UCI of "+engine["id"].capitalize(), "only_web":True, ITEMS: [], ACTION:{ TYPE: "socket_read", VALUE: engine["id"]+".uci"} }

                uci_item[ITEMS].append(editor_menu)

           
        return result


    def initialize_web_menu(self, message={}):

        message["update_menu"] = list(filter(lambda item:"only_board" not in item or item["only_board"] == False, self._build_menu_items()))
        
        if self._socket != None:
            self._socket.send_message(message)

    def start_child_module(self):

        if self._socket != None:
            self._socket.send_message({ "loading_screen":True })

    def end_child_module(self):

        self.initialize_web_menu()

        self.home_screen()

    def disconnect(self):

        if self._socket != None:
            self._socket.disconnect()

    def browser_connected(self):
        return self._browser_connected


Menu()

while True:
    time.sleep(.5)
    
#subprocess.call([sys.executable, consts.OPT_DIRECTORY + "/game/menu.legacy.py"])