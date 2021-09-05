# Bootup menu

import boardfunctions
import os
import sys
import time

# Power on sound
boardfunctions.beep(boardfunctions.SOUND_POWER_ON)
boardfunctions.clearSerial()
boardfunctions.initScreen()
time.sleep(2)
boardfunctions.ledsOff()

while True:
    menu = {
        'Lichess': 'Lichess',
        'Centaur': 'DGT Centaur',
        'Shutdown': 'Shutdown',
        'Reboot': 'Reboot'}
    boardfunctions.initialised = 0
    result = boardfunctions.doMenu(menu)
    if result == "Centaur":
        boardfunctions.clearScreen()
        os.chdir("/home/pi/centaur")
        os.system("/home/pi/centaur/centaur")
        sys.exit()
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
                os.chdir("/home/pi/centaur/py")
                os.system("/bin/python3 /home/pi/centaur/py/lichess.py current")
                sys.exit()

            livemenu = {'Rated': 'Rated', 'Unrated': 'Unrated'}
            result = boardfunctions.doMenu(livemenu)
            print(result)

            colormenu = {'Random': 'Random', 'Black': 'Black', 'White': 'White'}
            result = boardfunctions.doMenu(colormenu)
            print(result)

            timemenu = {'15': '15 Minutes', '30': '30 Minutes', '60': '60 Minutes'}
            result = boardfunctions.doMenu(timemenu)
            print(result)
