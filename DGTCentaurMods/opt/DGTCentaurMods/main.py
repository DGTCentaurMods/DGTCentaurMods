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

from DGTCentaurMods.classes import Log, SocketClient, CentaurScreen, CentaurBoard
from DGTCentaurMods.consts import consts, Enums, fonts
from DGTCentaurMods.lib import common

from pathlib import Path

import time, os, configparser, re, copy, importlib, shlex

LASTEST_TAG = common.get_lastest_tag()

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
ONLY_WEB = "only_web"
ONLY_BOARD = "only_board"
ID = "id"
DISABLED = "disabled"

# Menu items
# Proto version, shared between web & ePaper
MENU_ITEMS = [

    {   ID:"play", 
        LABEL:"Play",
        ITEMS: [
            {LABEL: "Resume last game", SHORT_LABEL: "Resume",
             ACTION: { TYPE: "socket_execute", VALUE: "uci_resume.py"} },
            {LABEL: "Play 1 vs 1", 
             ACTION:{ TYPE: "socket_execute", VALUE: "1vs1_module.py"} },
            {LABEL: "Play Lichess", 
             ACTION:{ TYPE: "socket_execute", VALUE: "lichess_module.py"} },
        ] }, 
    
    { LABEL:"Links", ONLY_WEB:True, ITEMS: [
            {LABEL: "Open Lichess position analysis", 
             ACTION :{ TYPE: "js", VALUE: '() => window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")' }},
            {LABEL: "Open Lichess PGN import page", 
             ACTION:{ TYPE: "js", VALUE: '() => window.open("https://lichess.org/paste", "_blank")' }},
            {LABEL: "View current PGN", 
             ACTION:{ TYPE: "js", VALUE: '() => me.viewCurrentPGN()' }},
        ]}, 
    
    { LABEL:"Settings", ONLY_WEB:True, ITEMS: [
        { LABEL:"🕸 Web settings", ONLY_WEB:True, ITEMS: [], TYPE: "subitem", ACTION:{TYPE: "js_variable", VALUE: "displaySettings"} },
        { LABEL:"🎵 Board sounds", ONLY_WEB:True, ACTION:{ TYPE: "socket_data", VALUE: "sounds_settings"}}, 
    ]},
    
    { LABEL:"Previous games", ONLY_WEB:True, ACTION:{ TYPE: "socket_data", VALUE: "previous_games"} }, 
    
    {   ID:"system", 
        LABEL:"System", ITEMS: [
            { LABEL: "📴 Power off board", SHORT_LABEL: "Power off",
              ACTION:{ TYPE: "socket_sys", "message": "A shutdown request has been sent to the board!", VALUE: "shutdown"}
            },
            { LABEL: "🌀 Reboot board", SHORT_LABEL: "Reboot",
              ACTION:{ TYPE: "socket_sys", "message": "A reboot request has been sent to the board!", VALUE: "reboot"}
            },
            { LABEL: "⚡ Restart service", ONLY_WEB:True,
              ACTION:{ TYPE: "socket_sys", "message": "A restart request has been sent to the board!", VALUE: "restart_service"}
            },
            { LABEL:"Wifi", ONLY_BOARD:True,
              ACTION:{ TYPE: "socket_execute", VALUE: "wifi_module"} },

            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },

            #{ LABEL:"Update", ONLY_BOARD:True,
            #  ACTION:{ TYPE: "script_execute", VALUE: "update_mod"} },

            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
            
            { LABEL: f"tag:{consts.TAG_RELEASE}", ONLY_BOARD:True, DISABLED:True, "font":"SMALL_FONT" },
            { LABEL: f"last:{LASTEST_TAG}", ONLY_BOARD:True, DISABLED:True, "font":"SMALL_FONT" },

            { TYPE: "divider", ONLY_WEB:True },
            
            { LABEL: "📋 Last log events", ONLY_WEB:True,
              ACTION:{ TYPE: "socket_sys", "message": None, VALUE: "log_events"}
            },

            { TYPE: "divider", ONLY_WEB:True },

            { LABEL: "✏ Edit configuration file", ONLY_WEB:True, ITEMS: [], ACTION:{ TYPE: "socket_read", VALUE: "centaur.ini"}},
            { ID:"uci", LABEL:"✏ Edit engines UCI", TYPE: "subitem", ITEMS: [], ONLY_WEB:True },
            { ID:"famous", LABEL:"✏ Edit famous PGN", TYPE: "subitem", ITEMS: [], ONLY_WEB:True },
        ] },

        # Current tag version label
        { LABEL: consts.EMPTY_LINE, ONLY_BOARD:True, DISABLED:True },
        { LABEL: f"tag:{consts.TAG_RELEASE}" if LASTEST_TAG == consts.TAG_RELEASE else "Update available!", ONLY_BOARD:True, DISABLED:True, "font":"SMALL_FONT" },
]

if os.path.exists(f"{consts.HOME_DIRECTORY}/centaur/centaur"):
    MENU_ITEMS.insert(len(MENU_ITEMS)-2, { LABEL:"Launch Centaur", SHORT_LABEL:"Centaur", ACTION:{ TYPE: "socket_sys", VALUE: "centaur"} })


class Menu:

    _browser_connected = False

    _is_root = False

    def home_screen(self):

        SCREEN.set_reversed(False)

        CENTAUR_BOARD.leds_off()

        self.draw_menu()
        #SCREEN.save_screen()

    def draw_menu(self):

        # TODO to be optimized...

        is_root = len(self._menu[NODES]) == 0

        current_row = 10 if is_root else 2
        current_index = 0

        #SCREEN.write_text(current_row-.7, "Choose one item", font=fonts.SMALL_FONT)

        if is_root:

            if not self._is_root:

                SCREEN.system_message('Welcome!')
                SCREEN.write_text(2, consts.EMPTY_LINE)
                SCREEN.write_text(3, consts.EMPTY_LINE)
                SCREEN.draw_fen(common.get_Centaur_FEN())
                SCREEN.write_text(current_row-1.2, consts.EMPTY_LINE)
        else:
            SCREEN.system_message(consts.EMPTY_LINE)

        self._is_root = is_root

        current_items = self._menu[CURRENT_NODE]+([{LABEL:consts.EMPTY_LINE}]*10)

        current_item_row = current_row

        # We draw all the visible items
        for item in current_items:

            SCREEN.write_text(current_row, item[SHORT_LABEL if SHORT_LABEL in item else LABEL], font=fonts.MAIN_FONT if "font" not in item else getattr(fonts, item["font"]))
            
            # Current selected item?
            if current_index == self._menu[CURRENT_INDEX]:
                current_item_row = current_row

            current_index = current_index +1
            current_row = current_row +1

            # Out of the screen?
            if current_row == 20:
                break

        # Then we draw the selected item
        y = current_item_row * CentaurScreen.HEADER_HEIGHT
        SCREEN.draw_rectangle(0,y,CentaurScreen.SCREEN_WIDTH -1,y+CentaurScreen.HEADER_HEIGHT, outline=0)
        

    def __init__(self):

        def _on_socket_request(data, socket):

            #Log.debug(data)
            try:
            
                #response = {}

                if "screen_message" in data:
                    SCREEN.home_screen(data["screen_message"])

                if "standby" in data:
                    if data["standby"]:
                        SCREEN.pause()
                    else:
                        SCREEN.unpause()
                        self.draw_menu()

                if "battery" in  data:
                    SCREEN.set_battery_value(data["battery"])

                if "web_menu" in data:
                    self.initialize_web_menu()

                if "web_move" in data:
                    # No game in progress - we send back the current FEN
                    self._socket.send_message({ "fen":common.get_Centaur_FEN() })

                if "web_button" in data:
                    CENTAUR_BOARD.push_button(Enums.Btn(data["web_button"]))

                if "pong" in data:
                    # Browser is connected (server ping)
                    self._browser_connected = True
                    #socket.send_message(response)

                if "sys" in data:
                   
                    command = data["sys"]

                    Log.debug(command)

                    if command == "homescreen":
                        CENTAUR_BOARD.push_button(Enums.Btn.BACK)

                    # The system actions are executed on server side
                    # We only handle the UI here (as the browser does)

                    if command=="reboot":
                        SCREEN.home_screen("Rebooting!")
                    
                    if command=="shutdown":
                        CENTAUR_BOARD.led_from_to(7,7)
                        SCREEN.home_screen("Bye!")
                        time.sleep(1)
                        CENTAUR_BOARD.sleep()

                    if command=="restart_service":
                        SCREEN.home_screen("Reloading!")

                    if command=="centaur":
                        SCREEN.home_screen("Loading Centaur!")
                        CENTAUR_BOARD.pause_events()
                    

                if "execute" in data:

                    command = data["execute"]

                    Log.debug(command)

                    match = re.search('1vs1_module|uci_resume|uci_module|famous_module|wifi_module|lichess_module', command)

                    if match != None:

                        script = match.group()

                        self.start_child_module()

                        module = importlib.import_module(name=f".modules.{script}", package=consts.MAIN_ID)
                   
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

        SCREEN.on_change(lambda image:self._socket.send_message({ "centaur_screen":image }))

        self._socket.send_message({ "ping":True, "loading_screen":False, "popup":"The service is up and running!" })

        self._menu = {
            CURRENT_INDEX: 0,
            NODES: [],
            NODE_INDEXES: [],
            ITEMS: self._build_menu_items(ONLY_WEB)
        }

        self._menu[CURRENT_NODE] = self._menu[ITEMS]

        self.home_screen()

        CENTAUR_BOARD.subscribe_events(self._key_callback, None, self._socket)

    def _key_callback(self, key_index):
        #print(key_index)

        #SCREEN.restore_screen()

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

        if key_index == Enums.Btn.TICK or key_index == Enums.Btn.PLAY:

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

                    if item_type == 'script_execute':

                        SCREEN.home_screen("Processing...")

                        # The server will excute the command
                        self._socket.send_request({'script':value})

                        time.sleep(3)

                        CENTAUR_BOARD.push_button(Enums.Btn.BACK)


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

                m[CURRENT_NODE] = nodes.pop()
                m[CURRENT_INDEX] = m[NODE_INDEXES].pop()

        # We bypass the disabled items
        if DISABLED in node[m[CURRENT_INDEX]] and node[m[CURRENT_INDEX]][DISABLED]:
            CENTAUR_BOARD.push_button(key_index)
        else:
            self.draw_menu()


    # Add engines and famous PGNs to proto menu
    def _build_menu_items(self, excluded_flag):

        result = []

        # Items to exclude
        for m in list(filter(lambda item:excluded_flag not in item or item[excluded_flag] == False, copy.deepcopy(MENU_ITEMS))):
            if ITEMS in m:
                menu_item = copy.deepcopy(m)
                menu_item[ITEMS] = list(filter(lambda item:excluded_flag not in item or item[excluded_flag] == False, m[ITEMS]))
                result.append(menu_item)
            else:
                result.append(m)
        
        play_item = next(filter(lambda item:ID in item and item[ID] == "play", result))
        sys_item = next(filter(lambda item:ID in item and item[ID] == "system", result))

        ENGINE_PATH = consts.OPT_DIRECTORY+"/engines"
        PGNS_PATH = consts.OPT_DIRECTORY+"/famous_pgns"

        def get_sections(uci_file):
            parser = configparser.ConfigParser()
            parser.read(uci_file)

            return list(map(lambda section:section, parser.sections()))

        # We read the available engines + their options
        engines = list(map(lambda f:{ID:Path(f.name).stem, "options":get_sections(f.path)}, 
                           filter(lambda f: f.name.endswith(".uci"), os.scandir(ENGINE_PATH))))
        
        # Stockfish has no configuration file (we might create one...)
        engines.append({ ID:"stockfish", "options":["1350","1400","1500","1600","1700","1800","2000","2200","2400","2600","2850"]})

        famous_pgns = list(map(lambda f:Path(f.name).stem, 
                           filter(lambda f: f.name.endswith(".pgn"), os.scandir(PGNS_PATH))))


        # Famous PGN menu item
        play_item[ITEMS].append({ LABEL: "Play famous games", SHORT_LABEL: "Famous games", TYPE: "subitem", 
                                   ITEMS:list(map(lambda pgn: { LABEL: "⭐ "+pgn.capitalize(), SHORT_LABEL:pgn.capitalize(), ACTION: { TYPE: "socket_execute", VALUE: f'famous_module.py "{pgn}.pgn"' }},famous_pgns)) })

        # Engines menu items
        for engine in engines:

            engine_menu = { LABEL: "Play "+engine[ID].capitalize(), SHORT_LABEL: engine[ID].capitalize(), TYPE: "subitem", ITEMS:[] }

            play_item[ITEMS].append(engine_menu)
            
            for option in engine["options"]:
                    
                engine_menu[ITEMS].append({
                        LABEL: "⭐ "+option.capitalize(), SHORT_LABEL:option.capitalize(),
                        ACTION: { TYPE: "socket_execute", "dialogbox": "color", VALUE: "uci_module.py {value} "+engine[ID]+' "'+option+'"' } })
                

        # Famous PGN editor menu items
        # UCI editor menu items
        # Only web
        if excluded_flag == ONLY_BOARD:

            famous_item = next(filter(lambda item:ID in item and item[ID] == "famous", sys_item[ITEMS]))

            for pgn in famous_pgns:

                editor_menu = { LABEL: 'Edit "'+pgn.capitalize()+'"', ONLY_WEB:True, ITEMS: [], ACTION:{ TYPE: "socket_read", VALUE: pgn+".pgn"} }
                famous_item[ITEMS].append(editor_menu)

            uci_item = next(filter(lambda item:ID in item and item[ID] == "uci", sys_item[ITEMS]))
            
            for engine in engines:

                if os.path.exists(f"{consts.OPT_DIRECTORY}/engines/{engine['id']}.uci"):

                    editor_menu = { LABEL: "Edit UCI of "+engine[ID].capitalize(), ONLY_WEB:True, ITEMS: [], ACTION:{ TYPE: "socket_read", VALUE: engine[ID]+".uci"} }

                    uci_item[ITEMS].append(editor_menu)

           
        return result


    def initialize_web_menu(self, message={}):

        message["update_menu"] = self._build_menu_items(ONLY_BOARD)

        if self._socket != None:
            self._socket.send_message(message)

    def start_child_module(self):

        if self._socket != None:
            self._socket.send_message({ 
                "loading_screen":True,
                "update_menu": [{
                LABEL:"← Back to main menu", 
                ACTION: { "type": "socket_sys", VALUE: "homescreen"}}]
            })

    def end_child_module(self):

        self.initialize_web_menu({"loading_screen":False, "fen":common.get_Centaur_FEN()})

        self.home_screen()

    def disconnect(self):

        if self._socket != None:
            self._socket.disconnect()

    def browser_connected(self):
        return self._browser_connected


Menu()

while True:
    time.sleep(.5)