from DGTCentaurMods.game.classes import Log, SocketClient
from DGTCentaurMods.game.consts import consts
from DGTCentaurMods.game.lib import common
from DGTCentaurMods.display import epd2in9d

import time, sys
import subprocess

class Menu:

    _processing = False
    _browser_connected = False

    def __init__(self):

        def _on_socket_request(data, socket):

            if (self._processing):
                return

            try:
            
                #response = {}

                UCI_MODULE_PATH = consts.OPT_DIRECTORY + "/game/uci_module.py"

                if "web_menu" in data:
                    self.initializeWebMenu()

                if "pong" in data:
                    # Browser is connected (server ping)
                    self._browser_connected = True
                    #socket.send_message(response)

                if "menu" in data:

                    action = data["menu"]

                    Log.debug(action)

                    if action == "uci_resume":
                        self._processing = True
                        self._socket.send_message({ "disable_menu":"play", "popup":"The board is being initialized..." })
                        last_uci = common.get_last_uci_command()
                        subprocess.call([sys.executable, UCI_MODULE_PATH]+last_uci.split())
                        self._processing = False
                        self.initializeWebMenu({ "popup":"The current game has been paused!" })

                    if action[:8] == "uci_maia":
                        self._processing = True
                        self._socket.send_message({ "disable_menu":"play", "popup":"The board is being initialized..." })
                        args = action.split()
                        args.pop(0)
                        subprocess.call([sys.executable, UCI_MODULE_PATH]+args)
                        self._processing = False
                        self.initializeWebMenu({ "popup":"The current game has been paused!" })

            except Exception as e:
                Log.exception(f"_on_socket_request:{e}")
                pass

        self._socket = SocketClient.get(on_socket_request=_on_socket_request)

        self._socket.send_message({ "ping":True, "popup":"The service is up and running!" })

    def clear_screen(self):
        epd = epd2in9d.EPD()
        epd.init()
        epd.Clear(0xff)

    def initializeWebMenu(self, message={}):
        message["enable_menu"] = "play"
        self._socket.send_message(message)

    def disconnect(self):
        self._socket.disconnect()

    def browser_connected(self):
        return self._browser_connected


menu = Menu()
menu.clear_screen()

time.sleep(1)

if menu.browser_connected():
    Log.info("At least one browser is connected, legacy menu is disabled.")
    menu.initializeWebMenu({ "popup":"Legacy menu has been disabled!" })
    while True:
        time.sleep(.5)
else:
    menu.disconnect()

    del menu

    subprocess.call([sys.executable, consts.OPT_DIRECTORY + "/game/menu.legacy.py"])