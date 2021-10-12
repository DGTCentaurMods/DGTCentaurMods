# Bootup menu

from DGTCentaurMods.board import boardfunctions
import os
import sys
import time
import pathlib

# Power on sound
boardfunctions.beep(boardfunctions.SOUND_POWER_ON)
boardfunctions.clearSerial()
boardfunctions.initScreen()
time.sleep(2)
boardfunctions.ledsOff()
boardfunctions.initialised = 0

while True:
    menu = {
        'Lichess': 'Lichess',
        'Centaur': 'DGT Centaur',
        'EmulateEB': 'e-Board',
        'Pairing': 'Start BT Pair',
        'WiFi': 'Wifi Conf',
        'Shutdown': 'Shutdown',
        'Reboot': 'Reboot'}
    result = boardfunctions.doMenu(menu)
    if result == "Centaur":
        boardfunctions.clearScreen()
        os.chdir("/home/pi/centaur")
        os.system("/home/pi/centaur/centaur")
        sys.exit()
    if result == "EmulateEB":
        boardfunctions.clearScreen()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/eboard.py")
    if result == "Pairing":
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/pair.py")
    if result == "WiFi":
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/wifi.py")
    if result == "Shutdown":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        boardfunctions.shutdown()
    if result == "Reboot":
        boardfunctions.clearScreen()
        boardfunctions.sleepScreen()
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        os.system("/sbin/shutdown -r now")
        sys.exit()
    if result == "BACK":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        boardfunctions.shutdown()
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
