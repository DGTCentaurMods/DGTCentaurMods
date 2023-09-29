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

from DGTCentaurMods.classes import CentaurScreen, CentaurBoard, LiveScript
from DGTCentaurMods.consts import Enums

import time

CENTAUR_BOARD = CentaurBoard.get()
SCREEN = CentaurScreen.get()

def handle_socket_requests(data):

    def _back_home():
        CENTAUR_BOARD.push_button(Enums.Btn.BACK)
        time.sleep(1)
        CENTAUR_BOARD.led_from_to(7,7)
        time.sleep(1)

    if "pong" in data:
        # Browser is connected (server ping)
        pass

    if "standby" in data:
        if data["standby"]:
            SCREEN.home_screen("Paused!")
            SCREEN.pause()
        else:
            SCREEN.unpause()
            SCREEN.home_screen("Welcome!")

    if "battery" in  data:
        SCREEN.set_battery_value(data["battery"])
        del data["battery"]

    if "sys" in data:
        
        command = data["sys"]

        del data["sys"]

        if command == "homescreen":
            CENTAUR_BOARD.push_button(Enums.Btn.BACK)

        # The system actions are executed on server side
        # We only handle the UI here (as the browser does)
        
        if command=="shutdown":
            _back_home()
            
            SCREEN.home_screen("Bye!")
            CENTAUR_BOARD.sleep()

        if command=="restart_service" or command=="restart_web_service":
            _back_home()

            CENTAUR_BOARD.leds_off()

            SCREEN.home_screen("Reloading!")

        if command=="centaur":
            _back_home()
            
            SCREEN.home_screen("Loading Centaur!")
            time.sleep(1)

            CENTAUR_BOARD.pause_events()
        
    if "live_script" in data:
        LiveScript.execute(data["live_script"] or "")
        del data["live_script"]