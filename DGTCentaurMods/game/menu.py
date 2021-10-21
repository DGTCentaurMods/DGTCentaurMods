from DGTCentaurMods.board import boardfunctions, network
from DGTCentaurMods.board import centaur
from DGTCentaurMods.display import epaper
from PIL import Image, ImageDraw, ImageFont
import time
import pathlib
import os
import sys
import threading

menuitem = 1
curmenu = None
selection = ""

event_key = threading.Event()

def keyPressed(id):
    # This function receives key presses
    global menuitem
    global curmenu
    global selection
    global event_key
    boardfunctions.beep(boardfunctions.SOUND_GENERAL)
    if id == boardfunctions.BTNDOWN:
        menuitem = menuitem + 1
    if id == boardfunctions.BTNUP:
        menuitem = menuitem - 1
    if id == boardfunctions.BTNTICK:
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
    if id == boardfunctions.BTNBACK:
        selection = "BACK"
        epaper.epd.HalfClear()
        event_key.set()
        return
    if id == boardfunctions.BTNHELP:
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
        boardfunctions.beep(boardfunctions.SOUND_GENERAL)
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
    epaper.epd.init()
    time.sleep(0.2)
    selection = ""
    curmenu = menu
    # Display the given menu
    epaper.clearScreen()
    menuitem = 1
    quickselect = 0
    boardfunctions.pauseEvents()
    res = boardfunctions.getBoardState()
    boardfunctions.unPauseEvents()
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
    event_key.wait()
    event_key.clear()
    return selection

# Turn Leds off, beep, clear DGT Centaur Serial
# Initialise the epaper display - after which functions in epaper.py are available but you can also draw to the
# image epaper.epaperbuffer to change the screen.
boardfunctions.ledsOff()
boardfunctions.beep(boardfunctions.SOUND_POWER_ON)
boardfunctions.clearSerial()
epaper.initEpaper(1)
# Subscribe to board events. First parameter is the function for key presses. The second is the function for
# field activity
boardfunctions.subscribeEvents(keyPressed, fieldActivity)


# Handle the menu structure
while True:
    menu = {
        'Centaur': 'DGT Centaur',
        'Lichess': 'Lichess',
        'Engines' : 'Engines',
        'EmulateEB': 'e-Board',
        'Cast' : 'Chromecast',
        'settings': 'Settings',
        'Support': 'Get support'}
    result = doMenu(menu)
    epaper.epd.init()
    time.sleep(0.2)
    if result == "BACK":
        boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
        #oardfunctions.shutdown()
    if result == "Cast":
        epaper.clearScreen()
        epaper.writeText(0,"Loading...")
        boardfunctions.pauseEvents()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../display/chromecast.py")
        boardfunctions.unPauseEvents()
    if result == "Centaur":
        epaper.clearScreen()
        epaper.writeText(0, "Loading...")
        time.sleep(1)
        boardfunctions.pauseEvents()
        os.chdir("/home/pi/centaur")
        os.system("sudo systemctl start centaur.service")
        # Once started we cannot return to DGTCentaurMods, we can kill that
        time.sleep(3)
        os.system("sudo systemctl stop DGTCentaurMods.service")
        sys.exit()
    if result == "EmulateEB":
        epaper.clearScreen()
        epaper.writeText(0, "Loading...")
        boardfunctions.pauseEvents()
        os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/eboard.py")
        boardfunctions.unPauseEvents()
    if result == "settings":
        setmenu = {
                'WiFi': 'Wifi Setup',
                'Pairing': 'Start BT Pair',
                'LichessAPI': 'Lichess API',
                'Shutdown': 'Shutdown',
                'Reboot': 'Reboot' }
        result = doMenu(setmenu)
        print(result)
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
                    boardfunctions.pauseEvents()
                    epaper.writeText(0, "Loading...")
                    os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/wifi.py")
                    boardfunctions.unPauseEvents()
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
            boardfunctions.pauseEvents()
            epaper.writeText(0, "Loading...")
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/pair.py")
            boardfunctions.unPauseEvents()
        if result == "LichessAPI":
            boardfunctions.pauseEvents()
            epaper.writeText(0, "Loading...")
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../config/lichesstoken.py")
            boardfunctions.unPauseEvents()
        if result == "Shutdown":
            boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
            epaper.epd.init()
            epaper.epd.HalfClear()
            time.sleep(5)
            epaper.stopEpaper()
            time.sleep(2)
            boardfunctions.pauseEvents()
            boardfunctions.shutdown()
        if result == "Reboot":
            boardfunctions.beep(boardfunctions.SOUND_POWER_OFF)
            epaper.epd.init()
            epaper.epd.HalfClear()
            time.sleep(5)
            epaper.stopEpaper()
            time.sleep(2)
            boardfunctions.pauseEvents()
            os.system("/sbin/shutdown -r now &")
            sys.exit()
    if result == "Lichess":
        lichessmenu = {'Current': 'Current', 'New': 'New Game'}
        result = doMenu(lichessmenu)
        print(result)
        # Current game will launch the screen for the current
        if (result != "BACK"):
            if (result == "Current"):
                epaper.clearScreen()
                epaper.writeText(0, "Loading...")
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
                            epaper.clearScreen()
                            epaper.writeText(0, "Loading...")
                            boardfunctions.pauseEvents()
                            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/lichess.py New {gtime} {gincrement} {rated} {color}")
                            boardfunctions.unPauseEvents()
    if result == "Engines":
        enginemenu = {'stockfish': 'Stockfish', 'CT800': 'CT800'}
        result = doMenu(enginemenu)
        print(result)
        if result == "CT800":
            ct800menu = {'white': 'White', 'black': 'Black', 'random': 'Random'}
            color = doMenu(ct800menu)
            print(color)
            # Current game will launch the screen for the current
            if (color != "BACK"):
                ratingmenu = {'1000': '1000 ELO', '1100': '1100 ELO', '1200': '1200 ELO', '1400': '1400 ELO', '1500': '1500 ELO', '1600': '1600 ELO', '1800': '1800 ELO', '2000': '2000 ELO', '2200': '2200 ELO', '2400': '2400 ELO'}
                elo = doMenu(ratingmenu)
                if elo != "BACK":
                    epaper.clearScreen()
                    epaper.writeText(0, "Loading...")
                    boardfunctions.pauseEvents()
                    os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/ct800.py " + color + " " + elo)
                    boardfunctions.unPauseEvents()
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
                    boardfunctions.pauseEvents()
                    os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + "/../game/stockfish.py " + color + " " + elo)
                    boardfunctions.unPauseEvents()
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


