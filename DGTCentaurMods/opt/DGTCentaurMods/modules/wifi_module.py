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

from DGTCentaurMods.classes import Log, CentaurBoard, CentaurScreen
from DGTCentaurMods.consts import consts, Enums, fonts
from DGTCentaurMods.lib import common

from DGTCentaurMods.classes.wpa_pyfi.scan import Cell
from DGTCentaurMods.classes.wpa_pyfi.network import Network

import os, time

exit_requested = False
keyboard_index = 0
current_input = ""
wifi = {}

SCREEN = CentaurScreen.get()
CENTAUR_BOARD = CentaurBoard.get()

KEYBOARDS = [
    'GFEDCBA ONMLKJIHWVUTSRQP     ZYX76543210      98                ',
    'gfedcba onmlkjihwvutsrqp     zyx76543210      98                ',
    'GFEDCBA ONMLKJIHWVUTSRQP     ZYX@#&%()[]$*+-=_:;  ,.?!/\\        ',
    'gfedcba onmlkjihwvutsrqp     zyx@#&%()[]$*+-=_:;  ,.?!/\\        ',
]

def main():

    global exit_requested
    global current_input
    global wifi

    INDEX = "index"
    NETWORKS = "networks"
    SELECTED = "selected"
    
    exit_requested = False
    current_input = ""
    wifi = {}

    # We get the current SSID
    try:
        current_ssid = os.popen("iwgetid -r").read()[:-1]
    except:
        current_ssid = None

    os.system(f"sudo chmod 666 {Network.WPA_SUPPLICANT_CONFIG}")
    os.system(f"sudo chmod 777 {os.path.dirname(Network.WPA_SUPPLICANT_CONFIG)}")

    def _scan_networks():

        global wifi

        SCREEN.write_text(7, "Scanning")
        SCREEN.write_text(8, "networks...")
    
        for row in range(9,20):
            SCREEN.write_text(row, consts.EMPTY_LINE)
        
        os.system("sudo iwlist wlan0 scan | grep ESSID > /dev/null")
        all_networks = list(Cell.all('wlan0'))
        
        networks = []
        #ssids = [current_ssid]
        ssids = []

        index = 0

        for n in all_networks:

            if len(n.ssid) and n.ssid not in ssids:
                ssids.append(n.ssid)

                networks.append(n)

                index += 1

        wifi = {NETWORKS: networks, INDEX: 0}

    def _print_wifi_ui():
        SCREEN.clear_area()

        SCREEN.write_text(2, "Current WIFI", bordered=True)
        
        if current_ssid:
            SCREEN.write_text(3, f'"{current_ssid}"')
        else:
            SCREEN.write_text(3, f'Not connected!')

        SCREEN.write_text(5, "Available networks", bordered=True)

        _scan_networks()
        _print_networks()

    def _print_current_password():
        SCREEN.write_text(13, current_input.replace(' ', '.'))

    def _print_networks():

        index = 0

        for row in range(7,20):
            SCREEN.write_text(row, consts.EMPTY_LINE)

        if len(wifi[NETWORKS]) == 0:
            SCREEN.write_text(6, "No networks")
            SCREEN.write_text(7, "found!")
        else:
            for n in wifi[NETWORKS]:
                SCREEN.write_text(index+6, f'{n.ssid} ({n.signal})', option=index == wifi[INDEX])
                index += 1

    def _password_field_callback(field_index, field_action):

        global current_input

        # Letter is validated when piece is placed
        if field_action == Enums.PieceAction.PLACE:

            CENTAUR_BOARD.led(field_index)

            char = KEYBOARDS[keyboard_index][63-field_index]

            SCREEN.write_text(1, char)

            current_input += char

            _print_current_password()

        return
    
    def _wifi_key_callback(key_index):
        global exit_requested
        global current_input

        if key_index == Enums.Btn.TICK and len(wifi[NETWORKS]) > 0:

            selected_network = wifi[NETWORKS][wifi[INDEX]]
            Log.info(f'Network "{selected_network.ssid}" selected!')

            wifi[SELECTED] = selected_network

            SCREEN.clear_area()
            SCREEN.draw_board(KEYBOARDS[keyboard_index], is_keyboard=True)

            SCREEN.write_text(10, "Enter the")
            SCREEN.write_text(11, "password for")
            SCREEN.write_text(12, f'"{selected_network.ssid}"', font=fonts.SMALL_FONT)

            network = Network.find(selected_network.ssid)

            if network:
                current_input = network.opts["psk"][1:-1]
                _print_current_password()

            CENTAUR_BOARD.subscribe_events(_password_key_callback, _password_field_callback)

            return
        
        if key_index == Enums.Btn.DOWN:
            wifi[INDEX] += 1
            if wifi[INDEX]==len(wifi[NETWORKS]):
                wifi[INDEX]=0
            _print_networks()
            return
        
        if key_index == Enums.Btn.UP:
            wifi[INDEX]  -= 1
            if wifi[INDEX] ==-1:
                wifi[INDEX]=len(wifi[NETWORKS]) -1
            _print_networks()
            return

        if key_index == Enums.Btn.BACK:
            CENTAUR_BOARD.unsubscribe_events()
            exit_requested = True

    def _password_key_callback(key_index):

        global exit_requested
        global keyboard_index
        global current_input

        if key_index == Enums.Btn.TICK:

            try:

                SCREEN.home_screen("Connecting...")

                Log.info(f'Connecting to "{wifi[SELECTED].ssid}" / "{current_input}"...')

                network = Network.for_cell(wifi[SELECTED], current_input, interface='wlan0')
                network.save()
                network.activate()
            except Exception as e:
                Log.exception(_password_key_callback, e)
                
                if current_ssid:
                    try:
                        Log.info(f'Connecting back to "{current_ssid}"...')
                             
                        network = Network.find(current_ssid)
                        network.activate()
                    except Exception as e:
                        Log.exception(_password_key_callback, e)
                        pass
                pass

            CENTAUR_BOARD.unsubscribe_events()
            CENTAUR_BOARD.unsubscribe_events()
            exit_requested = True

            return
        
        if key_index == Enums.Btn.UP:
            keyboard_index += 1
            if keyboard_index==len(KEYBOARDS):
                keyboard_index=0
            SCREEN.draw_board(KEYBOARDS[keyboard_index], is_keyboard=True)
            return
        
        if key_index == Enums.Btn.DOWN:
            keyboard_index -= 1
            if keyboard_index==-1:
                keyboard_index=len(KEYBOARDS) -1
            SCREEN.draw_board(KEYBOARDS[keyboard_index], is_keyboard=True)
            return
        
        if key_index == Enums.Btn.HELP:

            if len(current_input)>0:
                current_input = current_input[:len(current_input)-1]
                _print_current_password()

        if key_index == Enums.Btn.BACK:

            CENTAUR_BOARD.unsubscribe_events()
            _print_wifi_ui()
    
    _print_wifi_ui()

    CENTAUR_BOARD.subscribe_events(_wifi_key_callback)


    while exit_requested == False:
        time.sleep(.1)

if __name__ == '__main__':
    main()