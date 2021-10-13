# Bootup menu

from DGTCentaurMods.board import boardfunctions, network
import os
import sys
import time
import pathlib

# Power on sound
boardfunctions.beep(boardfunctions.SOUND_POWER_ON)
boardfunctions.clearSerial()
boardfunctions.initScreen()
boardfunctions.ledsOff()
boardfunctions.initialised = 0

while True:
    menu = {
        'Centaur': 'DGT Centaur',
        'Lichess': 'Lichess',
        'EmulateEB': 'e-Board',
        'Pairing': 'Start BT Pair',
        'WiFi': 'Wifi Conf',
        'Shutdown': 'Shutdown',
        'Reboot': 'Reboot',
        'Support': 'Get support'}
    result = boardfunctions.doMenu(menu)
    if result == "BACK":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        #oardfunctions.shutdown()
    if result == "Centaur":
        boardfunctions.clearScreen()
        os.chdir("/home/pi/centaur")
        os.system("sudo systemctl start centaur.service")
        # Once started we cannot return to DGTCentaurMods, we can kill that
        time.sleep(3)
        os.system("sudo systemctl stop DGTCentaurMods.service")
        sys.exit()
    if result == "EmulateEB":
        boardfunctions.clearScreen()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/eboard.py")
    if result == "Pairing":
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/pair.py")
    if result == "WiFi":
        wifimenu = {'wpa2': 'WPA2-PSK', 'wps': 'WPS Setup', 'recover': 'Recover wifi'}
        result = boardfunctions.doMenu(wifimenu)
        if (result != "BACK"):
            if (result == 'wpa2'):
                os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/wifi.py")
            if (result == 'wps'):
                if network.check_network():
                    #from DGTCentaurMods.display import epd2in9d
                    #epd = epd2in9d.EPD()
                    #epd.init()
                    IP = network.check_network()
                    boardfunctions.clearScreen()
                    boardfunctions.clearScreenBuffer()
                    boardfunctions.writeTextToBuffer(0, 'Network is up.')
                    boardfunctions.writeTextToBuffer(1, 'Press OK to')
                    boardfunctions.writeTextToBuffer(2, 'disconnect')
                    boardfunctions.writeText(4, IP)
                    time.sleep(10)
                    # TODO: Remove sleep() and wait to get OK button here
                    # execute connect
                else:
                    wpsMenu = {'connect': 'Connect wifi'}
                    result = boardfunctions.doMenu(wpsMenu)
                    if (result == 'connect'):
                        print('connect')
                        # TODO: Enable this afet we implement recovery :)
                        boardfunctions.writeText(0, 'Press WPS button')
                        #network.wps_connect()
        if (result == 'recover'):
            print() # placeholer
            # TODO: Build funtion in network.py to force restore wifi.
    if result == "Shutdown":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        boardfunctions.shutdown()
    if result == "Reboot":
        boardfunctions.clearScreen()
        boardfunctions.sleepScreen()
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        os.system("/sbin/shutdown -r now")
        sys.exit()
    if result == "Lichess":
        lichessmenu = {'Current': 'Current', 'New': 'New Game'}
        result = boardfunctions.doMenu(lichessmenu)
        print(result)
        # Current game will launch the screen for the current
        if (result != "BACK"):
            if (result == "Current"):
                boardfunctions.clearScreen()
                os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/lichess.py current")
                sys.exit()
            livemenu = {'Rated': 'Rated', 'Unrated': 'Unrated'}
            result = boardfunctions.doMenu(livemenu)
            if result == "Rated":
                rated = True
            else:
                rated = False
            colormenu = {'white': 'White', 'random': 'Random', 'black': 'Black'}
            result = boardfunctions.doMenu(colormenu)
            color = result
            timemenu = {'10 , 5': '10+5 minutes', '15 , 10': '15+10 minutes', '30': '30 minutes',
                        '30 , 20': '30+20 minutes', '60 , 20': '60+20 minutes'}
            result = boardfunctions.doMenu(timemenu)
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
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/lichess.py New {gtime} {gincrement} {rated} {color}")
    if result == "Support":
        from PIL import Image
        from DGTCentaurMods.display import epd2in9d
        epd = epd2in9d.EPD()
        epd.init()
        image = Image.new("1",( 128,296), 255)
        qr = Image.open(str(pathlib.Path(__file__).parent.resolve()) +"/../resources/qr-support.png")
        qr = qr.resize((128,128))
        image.paste(qr,(0,0))
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
        epd.display(epd.getbuffer(image))
        time.sleep(15)
        # TODO: implement wait for OK button here.
