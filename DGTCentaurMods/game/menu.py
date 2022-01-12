# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
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
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.board import *
from DGTCentaurMods.display import epaper
from PIL import Image, ImageDraw, ImageFont
import time
import pathlib
import os
import sys
import threading
import configparser

menuitem = 1
curmenu = None
selection = ""
centaur_software="/home/pi/centaur/centaur"

event_key = threading.Event()

def keyPressed(id):
    # This function receives key presses
    global menuitem
    global curmenu
    global selection
    global event_key
    epaper.epapermode = 1
    board.beep(board.SOUND_GENERAL)
    if id == board.BTNDOWN:
        menuitem = menuitem + 1
    if id == board.BTNUP:
        menuitem = menuitem - 1
    if id == board.BTNTICK:
        if not curmenu:
            selection = "BTNTICK"
            print(selection)
            #event_key.set()
            return
        c = 1
        r = ""
        for k, v in curmenu.items():
            if (c == menuitem):
                selection = k
                print(selection)
                epaper.epd.HalfClear()
                event_key.set()
                menuitem = 1
                return
            c = c + 1
    if id == board.BTNBACK:
        selection = "BACK"
        epaper.epd.HalfClear()
        event_key.set()
        return
    if id == board.BTNHELP:
        selection = "BTNHELP"
        epaper.epd.HalfClear()
        event_key.set()
        return
    if menuitem < 1:
        menuitem = 1
    if menuitem > len(curmenu):
        menuitem = len(curmenu)
    epaper.clearArea(0,0,17,295)
    draw = ImageDraw.Draw(epaper.epaperbuffer)
    draw.polygon([(2, (menuitem * 20) + 2), (2, (menuitem * 20) + 18),
                  (17, (menuitem * 20) + 10)], fill=0)
    draw.line((17, 0, 17, 295), fill=0, width=1)

quickselect = 0

def fieldActivity(id):
    # This function receives field activity. +fieldid for lift -fieldid for place down
    global quickselect
    global curmenu
    global selection
    if quickselect == 1 and (id < -15 and id > -32):
        board.beep(board.SOUND_GENERAL)
        menuitem = 1
        if quickselect == 1 and (id < -23 and id > -32):
            menuitem = (id * -1) - 23
        if quickselect == 1 and (id < -15 and id > -24):
            menuitem = (id * -1) - 7
        c = 1
        r = ""
        for k, v in curmenu.items():
            if (c == menuitem):
                selection = k
                event_key.set()
                menuitem = 1
                return
            c = c + 1

def doMenu(menu):
    # Draws a menu and waits for the response in the global variable 'selection'
    global menuitem
    global curmenu
    global selection
    global quickselect
    global event_key
    #epaper.epd.init()
    #time.sleep(0.7)
    selection = ""
    curmenu = menu
    # Display the given menu
    epaper.clearScreen()
    menuitem = 1
    quickselect = 0
    board.pauseEvents()
    res = board.getBoardState()
    board.unPauseEvents()
    # If 3rd and 4th ranks are empty then enable quick select by placing and releasing a piece
    if res[32] == 0 and res[33] == 0 and res[34] == 0 and res[35] == 0 and res[36] == 0 and res[37] == 0 and res[38] == 0 and res[39] == 0:
        if res[24] == 0 and res[25] == 0 and res[26] == 0 and res[27] == 0 and res[28] == 0 and res[29] == 0 and res[30] == 0 and res[31] == 0:
            quickselect = 1
    row = 1
    for k, v in menu.items():
        epaper.writeText(row,"    " + str(v))
        row = row + 1
    epaper.clearArea(0,0,17,295)
    draw = ImageDraw.Draw(epaper.epaperbuffer)
    draw.polygon([(2, (menuitem * 20) + 2), (2, (menuitem * 20) + 18),
                  (17, (menuitem * 20) + 10)], fill=0)
    draw.line((17,0,17,295), fill=0, width=1)
    print("drawn")
    event_key.wait()
    event_key.clear()
    return selection

# Turn Leds off, beep, clear DGT Centaur Serial
# Initialise the epaper display - after which functions in epaper.py are available but you can also draw to the
# image epaper.epaperbuffer to change the screen.
board.ledsOff()
board.beep(board.SOUND_POWER_ON)
board.clearSerial()
epaper.initEpaper(1)
# Subscribe to board events. First parameter is the function for key presses. The second is the function for
# field activity
board.subscribeEvents(keyPressed, fieldActivity)


# Handle the menu structure
while True:
    menu = {}
    if os.path.exists(centaur_software):
        centaur_item = {'Centaur': 'DGT Centaur'}
        menu.update(centaur_item)
    if centaur.lichess_api:
        lichess_item = {'Lichess': 'Lichess'}
        menu.update(lichess_item)
    menu.update({
            'Engines' : 'Engines',
            'EmulateEB': 'e-Board',
            'Cast' : 'Chromecast',
            'settings': 'Settings',
            'Support': 'Get support'})
    result = doMenu(menu)
    epaper.epd.init()
    time.sleep(1.5)
    if result == "BACK":
        board.beep(board.SOUND_POWER_OFF)
        #oardfunctions.shutdown()
    if result == "Cast":
        epaper.clearScreen()
        epaper.writeText(0,"Loading...")
        board.pauseEvents()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../display/chromecast.py")
        board.unPauseEvents()
    if result == "Centaur":
        epaper.clearScreen()
        epaper.writeText(0, "Loading...")
        time.sleep(1)
        board.pauseEvents()
        board.ser.close()
        time.sleep(1)
        os.chdir("/home/pi/centaur")
        #os.system("sudo systemctl start centaur.service")
        os.system("sudo ./centaur")
        # Once started we cannot return to DGTCentaurMods, we can kill that
        time.sleep(3)
        os.system("sudo systemctl stop DGTCentaurMods.service")
        sys.exit()
    if result == "EmulateEB":
        boardmenu = {
            'dgtclassic' : 'DGT REVII',
            'millenium' : 'Millenium',
        }
        result = doMenu(boardmenu)
        if result == "dgtclassic":
            epaper.clearScreen()
            epaper.writeText(0, "Loading...")
            board.pauseEvents()
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/eboard.py")
            board.unPauseEvents()
        if result == "millenium":
            epaper.clearScreen()
            epaper.writeText(0, "Loading...")
            board.pauseEvents()
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/millenium.py")
            board.unPauseEvents()
    if result == "settings":
        setmenu = {
                'WiFi': 'Wifi Setup',
                'Pairing': 'BT Pair',
                'Sound': 'Sound',
                'LichessAPI': 'Lichess API',
                'Shutdown': 'Shutdown',
                'Reboot': 'Reboot' }
        result = doMenu(setmenu)
        print(result)
        if result == "Sound":
            soundmenu = {'On': 'On', 'Off': 'Off'}
            epaper.epd.init()
            time.sleep(0.5)
            result = doMenu(soundmenu)
            if result == "On":
                centaur.set_sound("on")
            if result == "Off":
                centaur.set_sound("off")
            epaper.epd.init()
            time.sleep(0.5)
        if result == "WiFi":
            if network.check_network():
                wifimenu = {'wpa2': 'WPA2-PSK', 'wps': 'WPS Setup'}
            else:
                wifimenu = {'wpa2': 'WPA2-PSK', 'wps': 'WPS Setup', 'recover': 'Recover wifi'}
            if network.check_network():
                cmd = "sudo sh -c \"" + str(pathlib.Path(__file__).parent.resolve()) + "/../scripts/wifi_backup.sh backup\""
                print(cmd)
                centaur.shell_run(cmd)
            result = doMenu(wifimenu)
            if (result != "BACK"):
                if (result == 'wpa2'):
                    board.pauseEvents()
                    epaper.writeText(0, "Loading...")
                    os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/wifi.py")
                    board.unPauseEvents()
                if (result == 'wps'):
                    if network.check_network():
                        selection = ""
                        curmenu = None
                        IP = network.check_network()
                        epaper.clearScreen()
                        epaper.writeText(0, 'Network is up.')
                        epaper.writeText(1, 'Press OK to')
                        epaper.writeText(2, 'disconnect')
                        epaper.writeText(4, IP)
                        timeout = time.time() + 15
                        while time.time() < timeout:
                            if selection == "BTNTICK":
                                network.wps_disconnect_all()
                                break
                            time.sleep(2)
                    else:
                        wpsMenu = {'connect': 'Connect wifi'}
                        result = doMenu(wpsMenu)
                        if (result == 'connect'):
                            epaper.clearScreen()
                            epaper.writeText(0, 'Press WPS button')
                            network.wps_connect()
                if (result == 'recover'):
                    selection=""
                    cmd = "sudo sh -c \"" + str(pathlib.Path(__file__).parent.resolve()) + "/../scripts/wifi_backup.sh restore\""
                    centaur.shell_run(cmd)
                    print(cmd)
                    timeout = time.time() + 20
                    epaper.clearScreen()
                    epaper.writeText(0, 'Waiting for')
                    epaper.writeText(1, 'network...')
                    while not network.check_network() and time.time() < timeout:
                        time.sleep(1)
                    if not network.check_network():
                        epaper.writeText(1, 'Failed to restore...')
                        time.sleep(4)

        if result == "Pairing":
            board.pauseEvents()
            epaper.writeText(0, "Loading...")
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/pair.py")
            board.unPauseEvents()
        if result == "LichessAPI":
            board.pauseEvents()
            epaper.writeText(0, "Loading...")
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/lichesstoken.py")
            board.unPauseEvents()
        if result == "Shutdown":
            board.beep(board.SOUND_POWER_OFF)
            epaper.epd.init()
            epaper.epd.HalfClear()
            time.sleep(5)
            epaper.stopEpaper()
            time.sleep(2)
            board.pauseEvents()
            board.shutdown()
        if result == "Reboot":
            board.beep(board.SOUND_POWER_OFF)
            epaper.epd.init()
            epaper.epd.HalfClear()
            time.sleep(5)
            epaper.stopEpaper()
            time.sleep(2)
            board.pauseEvents()
            os.system("/sbin/shutdown -r now &")
            sys.exit()
    if result == "Lichess":
        livemenu = {'Rated': 'Rated', 'Unrated': 'Unrated'}
        result = doMenu(livemenu)
        if result != "BACK":
            if result == "Rated":
                rated = True
            else:
                rated = False
            colormenu = {'random': 'Random', 'white': 'White', 'black': 'Black'}
            result = doMenu(colormenu)
            if result != "BACK":
                color = result
                timemenu = {'10 , 5': '10+5 minutes', '15 , 10': '15+10 minutes', '30': '30 minutes',
                            '30 , 20': '30+20 minutes', '60 , 20': '60+20 minutes'}
                result = doMenu(timemenu)
                if result != "BACK":
                    if result == '10 , 5':
                        gtime = '10'
                        gincrement = '5'
                    if result == '15 , 10':
                        gtime = '15'
                        gincrement = '10'
                    if result == '30':
                        gtime = '30'
                        gincrement = '0'
                    if result == '30 , 20':
                        gtime = '30'
                        gincrement = '20'
                    if result == "60 , 20":
                        gtime = '60'
                        gincrement = '20'
                    epaper.clearScreen()
                    epaper.writeText(0, "Loading...")
                    board.pauseEvents()
                    os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/lichess.py New " + str(gtime) + " " + str(gincrement) + " " + str(rated) + " " + str(color))
                    board.unPauseEvents()
    if result == "Engines":
        enginemenu = {'stockfish': 'Stockfish'}
        # Pick up the engines from the engines folder and build the menu
        enginepath = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
        enginefiles = os.listdir(enginepath)
        enginefiles = list(filter(lambda x: os.path.isfile(enginepath + x), os.listdir(enginepath)))
        print(enginefiles)
        for f in enginefiles:
            fn = str(f)
            if '.uci' not in fn:
                # If this file is not .uci then assume it is an engine
                enginemenu[fn] = fn
        result = doMenu(enginemenu)
        print(result)
        if result == "stockfish":
            sfmenu = {'white': 'White', 'black': 'Black', 'random': 'Random'}
            color = doMenu(sfmenu)
            print(color)
            # Current game will launch the screen for the current
            if (color != "BACK"):
                ratingmenu = {'2850': 'Pure', '1350': '1350 ELO', '1500': '1500 ELO', '1700': '1700 ELO', '1800': '1800 ELO', '2000': '2000 ELO', '2200': '2200 ELO', '2400': '2400 ELO', '2600': '2600 ELO'}
                elo = doMenu(ratingmenu)
                if elo != "BACK":
                    epaper.clearScreen()
                    epaper.writeText(0, "Loading...")
                    board.pauseEvents()
                    os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/stockfish.py " + color + " " + elo)
                    board.unPauseEvents()
        else:
            if result != "BACK":
                # There are two options here. Either a file exists in the engines folder as enginename.uci which will give us menu options, or one doesn't and we run it as default
                enginefile = enginepath + result
                ucifile = enginepath + result + ".uci"
                cmenu = {'white': 'White', 'black': 'Black', 'random': 'Random'}
                color = doMenu(cmenu)
                # Current game will launch the screen for the current
                if (color != "BACK"):
                    if os.path.exists(ucifile):
                        # Read the uci file and build a menu
                        config = configparser.ConfigParser()
                        config.read(ucifile)
                        print(config.sections())
                        smenu = {}
                        for sect in config.sections():
                            smenu[sect] = sect
                        sec = doMenu(smenu)
                        if sec != "BACK":
                            epaper.clearScreen()
                            epaper.writeText(0, "Loading...")
                            board.pauseEvents()
                            print(str(pathlib.Path(__file__).parent.resolve()) + "/../game/uci.py " + color + " \"" + result + "\"" + " \"" + sec+ "\"")
                            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/uci.py " + color + " \"" + result + "\"" + " \"" + sec+ "\"")
                            board.unPauseEvents()
                    else:
                        # With no uci file we just call the engine
                        epaper.clearScreen()
                        epaper.writeText(0, "Loading...")
                        board.pauseEvents()
                        print(str(pathlib.Path(__file__).parent.resolve()) + "/../game/uci.py " + color + " \"" + result + "\"")
                        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/uci.py " + color + " \"" + result + "\"")
                        board.unPauseEvents()
    if result == "Support" or result == "BTNHELP":
        selection = ""
        epaper.clearScreen()
        qr = Image.open(str(pathlib.Path(__file__).parent.resolve()) +"/../resources/qr-support.png")
        qr = qr.resize((128,128))
        epaper.epaperbuffer.paste(qr,(0,0))
        timeout = time.time() + 15
        while selection == "" and time.time() < timeout:
            if selection == "BTNTICK":
                break
        epaper.epd.init()
        time.sleep(0.5)


