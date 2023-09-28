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
from DGTCentaurMods.lib import common, sys_requests
from DGTCentaurMods.consts import menu

from DGTCentaurMods.consts.latest_tag import LASTEST_TAG

import time, os, re, importlib, shlex

CENTAUR_BOARD = CentaurBoard.get()
SCREEN = CentaurScreen.get()
SOCKET = SocketClient.connect_local_server()

_CURRENT_INDEX = "current_index"
_CURRENT_NODE = "current_node"
_CURRENT_VALUE = "current_value"
_NODE_INDEXES = "node_indexes"
_NODES = "nodes"

class Main:

    _is_root:bool = False

    def refresh_screen(self):

        SCREEN.set_reversed(False)
        SCREEN.clear_area()

        CENTAUR_BOARD.leds_off()

        self._is_root = False

        self.print_menu()
        #SCREEN.save_screen()

    def print_menu(self):

        # TODO to be optimized...
        is_root = len(self._menu[_NODES]) == 0

        current_row = 10 if is_root else 2
        current_index = 0

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

        current_items = self._menu[_CURRENT_NODE]+([{menu.Tag.LABEL:consts.EMPTY_LINE}]*20)

        current_item_row = current_row

        # We draw all the visible items
        for item in current_items:

            current_label = item[menu.Tag.SHORT_LABEL if menu.Tag.SHORT_LABEL in item else menu.Tag.LABEL]

            SCREEN.write_text(current_row, current_label, font=fonts.MAIN_FONT if "font" not in item else getattr(fonts, item["font"]))
            
            # Current selected item?
            if current_index == self._menu[_CURRENT_INDEX]:
                CENTAUR_BOARD.set_current_menu(current_label)
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

        Log.info(f"Starting {consts.MAIN_ID} service...")

        def _on_socket_request(data, socket:SocketClient._SocketClient):
            try:

                # Common sys requests handling
                sys_requests.handle_socket_requests(data)

                if "screen_message" in data:
                    SCREEN.home_screen(data["screen_message"])

                if "web_menu" in data:
                    self.initialize_web_menu()

                if "web_move" in data:
                    # No game in progress - we send back the current FEN
                    socket.send_web_message({ "fen":common.get_Centaur_FEN() })

                if "web_button" in data:
                    CENTAUR_BOARD.push_button(Enums.Btn(data["web_button"]))

                if "plugin_execute" in data:

                    plugin = data["plugin_execute"]

                    if os.path.exists(consts.PLUGINS_DIRECTORY+"/"+plugin+".py"):

                        self.start_child_module()

                        try:
                            module = importlib.import_module(name=f".plugins.{plugin}", package=consts.MAIN_ID)
                            importlib.reload(module)

                            class_ = getattr(module, plugin)

                            instance = class_(plugin)

                            instance.start()

                            socket.send_web_message({ "loading_screen":False })

                            while instance._running():
                                time.sleep(0.1)

                            del instance
                            del class_
                            del module
                        except:
                            socket.send_web_message({ "script_output":Log.last_exception() })
                            pass

                        self.end_child_module()

                    else:
                        Log.info(f'The plugin "{plugin}" does not exists!')
                
                if "execute" in data:

                    command = data["execute"]

                    match = re.search('1vs1_module|uci_resume|uci_module|famous_module|wifi_module|lichess_module', command)

                    if match != None:

                        script = match.group()

                        Log.info(f'Starting module "{script}"...')

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

                        Log.info(f'Stopping module "{script}"...')

                        self.end_child_module()

            except Exception as e:
                Log.exception(_on_socket_request, e)
                pass

        SOCKET.initialize(on_socket_request=_on_socket_request)

        SCREEN.on_change(lambda image:SOCKET.send_web_message({ "centaur_screen":image }))

        self.initialize_web_menu({ "ping":True, "loading_screen":False, "popup":"The service is up and running!" })

        self._menu = {
            _CURRENT_INDEX: 0,
            _NODES: [],
            _NODE_INDEXES: [],
            menu.Tag.ITEMS: menu.get(menu.Tag.ONLY_BOARD)
        }

        self._menu[_CURRENT_NODE] = self._menu[menu.Tag.ITEMS]

        self.refresh_screen()

        CENTAUR_BOARD.subscribe_events(self._key_callback)

        Log.info(f"Service {consts.MAIN_ID} up and running.")

    def _key_callback(self, key):

        m = self._menu

        node = m[_CURRENT_NODE]
        index = m[_CURRENT_INDEX]

        if key == Enums.Btn.UP:
            if index>0:
                m[_CURRENT_INDEX] = index-1
            else:
                m[_CURRENT_INDEX] = len(node)-1

        if key == Enums.Btn.DOWN:

            if index<len(node)-1:
                m[_CURRENT_INDEX] = index+1
            else:
                m[_CURRENT_INDEX] = 0

        if key == Enums.Btn.TICK or key == Enums.Btn.PLAY:

            if menu.Tag.ITEMS in node[index]:
                m[_CURRENT_NODE] = node[index][menu.Tag.ITEMS]
                m[_CURRENT_INDEX] = 0
                m[_NODES].append(node)
                m[_NODE_INDEXES].append(index)

            else:

                if menu.Tag.ACTION in node[index] and menu.Tag.VALUE in node[index][menu.Tag.ACTION]:

                    value = node[index][menu.Tag.ACTION][menu.Tag.VALUE]
                    item_type = node[index][menu.Tag.ACTION][menu.Tag.TYPE]

                    if item_type == 'color':

                        value = m[_CURRENT_VALUE].replace("{value}", value)

                        SOCKET.send_request({'execute':value})

                    if item_type == 'socket_sys':
                        # The server will excute the command
                        SOCKET.send_request({'sys':value})

                    if item_type == 'script_execute':

                        SCREEN.home_screen("Processing...")

                        # The server will excute the command
                        SOCKET.send_request({'script':value})

                        time.sleep(3)

                        CENTAUR_BOARD.push_button(Enums.Btn.BACK)

                    if item_type == 'socket_plugin':
                        SOCKET.send_request({'plugin_execute':value})

                    if item_type == 'socket_execute':

                        if "dialogbox" in node[index][menu.Tag.ACTION]:

                            # TODO align the design with the generic JS version
                            m[_CURRENT_NODE] = [
                                { menu.Tag.LABEL: "Play white",
                                menu.Tag.ACTION:{ menu.Tag.TYPE: "color", menu.Tag.VALUE: "white"}
                                },
                                { menu.Tag.LABEL: "Play black",
                                menu.Tag.ACTION:{ menu.Tag.TYPE: "color", menu.Tag.VALUE: "black"}
                                },
                            ]
                            m[_CURRENT_INDEX] = 0
                            m[_NODES].append(node)

                            m[_NODE_INDEXES].append(index)

                            m[_CURRENT_VALUE] = value

                        else:
                            SOCKET.send_request({'execute':value})

        if key == Enums.Btn.BACK:
            nodes = m[_NODES]
            if len(nodes) >0:

                m[_CURRENT_NODE] = nodes.pop()
                m[_CURRENT_INDEX] = m[_NODE_INDEXES].pop()

            else:
                m[_CURRENT_INDEX] = 0

        # We bypass the disabled items
        if m[_CURRENT_INDEX]<len(node) and menu.Tag.DISABLED in node[m[_CURRENT_INDEX]] and node[m[_CURRENT_INDEX]][menu.Tag.DISABLED]:
            # Because of the temporization, push might be ignored if too fast.
            # We force the push.
            CENTAUR_BOARD.push_button(key, True)
        else:
            self.print_menu()

    def initialize_web_menu(self, message={}):

        message["update_menu"] = menu.get(menu.Tag.ONLY_WEB)

        message["release"] = {
            "tag":consts.TAG_RELEASE,
            "need_update":LASTEST_TAG != consts.TAG_RELEASE,
            "latest_tag":LASTEST_TAG
        }

        SOCKET.send_web_message(message)

    def start_child_module(self):

        SCREEN.clear_area()
        SCREEN.write_text(8, "Loading...")
    
        SOCKET.send_web_message({ 
            "loading_screen":True,
            "update_menu": menu.get(menu.Tag.ONLY_WEB, ["homescreen", "links", "settings", "system"])
        })

    def end_child_module(self):

        self.initialize_web_menu({"loading_screen":False, "fen":common.get_Centaur_FEN()})

        self.refresh_screen()


if os.path.exists(f"{consts.HOME_DIRECTORY}/{consts.MAIN_ID}_latest.deb"):

    SERVICE_LOCKED = "Service locked: one update in progress..."

    Log.info(SERVICE_LOCKED)
    print(SERVICE_LOCKED)

    time.sleep(3)
    SCREEN.home_screen()
    SCREEN.write_text(10, "Update")
    SCREEN.write_text(11, "in progress...")
    SCREEN.write_text(13, "Please wait!")
    time.sleep(3)

    exit()
else:
    Main()

while True:
    time.sleep(.5)