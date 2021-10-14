from DGTCentaurMods.board import boardfunctions, network
from DGTCentaurMods.board import epaper
from PIL import Image, ImageDraw, ImageFont
import time
import pathlib
import os
import sys

menuitem = 1
curmenu = None
selection = ""

def keyPressed(id):
    # This function receives key presses
    global menuitem
    global curmenu
    global selection
    boardfunctions.beep(boardfunctions.SOUND_GENERAL)
    if id == boardfunctions.BTNDOWN:
        menuitem = menuitem + 1
    if id == boardfunctions.BTNUP:
        menuitem = menuitem - 1
    if id == boardfunctions.BTNTICK:
        c = 1
        r = ""
        for k, v in curmenu.items():
            if (c == menuitem):
                selection = k
                menuitem = 1
                return
            c = c + 1
    if id == boardfunctions.BTNBACK:
        selection = "BACK"
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
    if quickselect == 1 and (id < -23 and id > -32):
        boardfunctions.beep(boardfunctions.SOUND_GENERAL)
        menuitem = (id * -1) - 23
        c = 1
        r = ""
        for k, v in curmenu.items():
            if (c == menuitem):
                selection = k
                menuitem = 1
                return
            c = c + 1

def doMenu(menu):
    # Draws a menu and waits for the response in the global variable 'selection'
    global menuitem
    global curmenu
    global selection
    global quickselect
    selection = ""
    curmenu = menu
    # Display the given menu
    epaper.clearScreen()
    menuitem = 1
    quickselect = 0
    boardfunctions.pauseEvents()
    res = boardfunctions.getBoardState()
    boardfunctions.unPauseEvents()
    if res[32] == 0 and res[33] == 0 and res[34] == 0 and res[35] == 0 and res[36]==0 and res[37] == 0 and res[38] == 0 and res[39] == 0:
        # If the 4th rank is empty then enable quick select mode. Then we can choose a menu option by placing and releasing a piece
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
    while selection == "":
        time.sleep(0.1)
    return selection

# Turn Leds off, beep, clear DGT Centaur Serial
# Initialise the epaper display - after which functions in epaper.py are available but you can also draw to the
# image epaper.epaperbuffer to change the screen.
boardfunctions.ledsOff()
boardfunctions.beep(boardfunctions.SOUND_POWER_ON)
boardfunctions.clearSerial()
epaper.initEpaper()
# Subscribe to board events. First parameter is the function for key presses. The second is the function for
# field activity
boardfunctions.subscribeEvents(keyPressed, fieldActivity)


# Handle the menu structure
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
    result = doMenu(menu)
    if result == "BACK":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        #oardfunctions.shutdown()
    if result == "Centaur":
        epaper.clearScreen()
        boardfunctions.pauseEvents()
        os.chdir("/home/pi/centaur")
        os.system("sudo systemctl start centaur.service")
        # Once started we cannot return to DGTCentaurMods, we can kill that
        time.sleep(3)
        os.system("sudo systemctl stop DGTCentaurMods.service")
        sys.exit()
    if result == "EmulateEB":
        epaper.clearScreen()
        boardfunctions.pauseEvents()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/eboard.py")
        boardfunctions.unPauseEvents()
    if result == "Pairing":
        boardfunctions.pauseEvents()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/pair.py")
        boardfunctions.unPauseEvents()
    if result == "WiFi":
        wifimenu = {'wpa2': 'WPA2-PSK', 'wps': 'WPS Setup', 'recover': 'Recover wifi'}
        result = doMenu(wifimenu)
        if (result != "BACK"):
            if (result == 'wpa2'):
                boardfunctions.pauseEvents()
                os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/wifi.py")
                boardfunctions.unPauseEvents()
            if (result == 'wps'):
                if network.check_network():
                    #from DGTCentaurMods.display import epd2in9d
                    #epd = epd2in9d.EPD()
                    #epd.init()
                    IP = network.check_network()
                    epaper.clearScreen()
                    epaper.writeText(0, 'Network is up.')
                    epaper.writeText(1, 'Press OK to')
                    epaper.writeText(2, 'disconnect')
                    epaper.writeText(4, IP)
                    time.sleep(10)
                    # TODO: Remove sleep() and wait to get OK button here
                    # execute connect
                else:
                    wpsMenu = {'connect': 'Connect wifi'}
                    result = doMenu(wpsMenu)
                    if (result == 'connect'):
                        print('connect')
                        # TODO: Enable this afet we implement recovery :)
                        epaper.writeText(0, 'Press WPS button')
                        #network.wps_connect()
        if (result == 'recover'):
            print() # placeholer
            # TODO: Build funtion in network.py to force restore wifi.
    if result == "Shutdown":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        boardfunctions.pauseEvents()
        boardfunctions.shutdown()
    if result == "Reboot":
        epaper.clearScreen()
        epaper.stopEpaper()
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        boardfunctions.pauseEvents()
        os.system("/sbin/shutdown -r now")
        sys.exit()
    if result == "Lichess":
        lichessmenu = {'Current': 'Current', 'New': 'New Game'}
        result = doMenu(lichessmenu)
        print(result)
        # Current game will launch the screen for the current
        if (result != "BACK"):
            if (result == "Current"):
                epaper.clearScreen()
                boardfunctions.pauseEvents()
                os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/lichess.py current")
                boardfunctions.unPauseEvents()
            else:
                livemenu = {'Rated': 'Rated', 'Unrated': 'Unrated'}
                result = doMenu(livemenu)
                if result != "BACK":
                    if result == "Rated":
                        rated = True
                    else:
                        rated = False
                    colormenu = {'white': 'White', 'random': 'Random', 'black': 'Black'}
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
                            boardfunctions.pauseEvents()
                            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/lichess.py New {gtime} {gincrement} {rated} {color}")
                            boardfunctions.unPauseEvents()
    if result == "Support":
        epaper.clearScreen()
        qr = Image.open(str(pathlib.Path(__file__).parent.resolve()) +"/../resources/qr-support.png")
        qr = qr.resize((128,128))
        epaper.epaperbuffer.paste(qr,(0,0))
        time.sleep(15)
        # TODO: implement wait for OK button here.


