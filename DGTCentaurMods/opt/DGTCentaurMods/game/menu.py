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

import configparser
import os
import pathlib
import sys
import threading
import time
import logging
import urllib.request
import json
import socket
import subprocess
import os
from DGTCentaurMods.display.ui_components import AssetManager

try:
    logging.basicConfig(level=logging.DEBUG, filename="/home/pi/debug.log",filemode="w")
except:
    logging.basicConfig(level=logging.DEBUG)

from DGTCentaurMods.board import *
from DGTCentaurMods.display import epaper
from PIL import Image, ImageDraw, ImageFont

menuitem = 1
curmenu = None
selection = ""
centaur_software = "/home/pi/centaur/centaur"

event_key = threading.Event()


def keyPressed(id):
    # This functiion receives key presses
    global shift
    global menuitem
    global curmenu
    global selection
    global event_key
    global idle
    epaper.epapermode = 1    
    if idle:
        if id == board.BTNTICK:
            event_key.set()
            return
    else:
        if id == board.BTNTICK:
            if not curmenu:
                selection = "BTNTICK"
                #print(selection)
                # event_key.set()
                return
            c = 1
            r = ""
            for k, v in curmenu.items():
                if c == menuitem:
                    selection = k
                    #print(selection)
                    event_key.set()
                    menuitem = 1
                    return
                c = c + 1

        if id == board.BTNLONGPLAY:
            board.shutdown()
            return
        if id == board.BTNDOWN:
            menuitem = menuitem + 1
        if id == board.BTNUP:
            menuitem = menuitem - 1
        if id == board.BTNBACK:
            selection = "BACK"
            event_key.set()
            return
        if id == board.BTNHELP:
            selection = "BTNHELP"
            event_key.set()
            return
        if menuitem < 1:
            menuitem = len(curmenu)
        if menuitem > len(curmenu):
            menuitem = 1       
        epaper.clearArea(0, 20 + shift, 17, 295)
        draw = ImageDraw.Draw(epaper.epaperbuffer)
        draw.polygon(
            [
                (2, (menuitem * 20 + shift) + 2),
                (2, (menuitem * 20) + 18 + shift),
                (17, (menuitem * 20) + 10 + shift),
            ],
            fill=0,
        )
        draw.line((17, 20 + shift, 17, 295), fill=0, width=1)


quickselect = 0

def doMenu(menu, title=None):
    # Draws a menu and waits for the response in the global variable 'selection'
    global shift
    global menuitem
    global curmenu
    global selection
    global quickselect
    global event_key
    epaper.epapermode = 0
    epaper.clearScreen()  
    
    selection = ""
    curmenu = menu
    # Display the given menu
    menuitem = 1
    quickselect = 0    

    quickselect = 1    
    if title:
        row = 2
        shift = 20
        epaper.writeMenuTitle("[ " + title + " ]")
    else:
        shift = 0
        row = 1
    # Print a fresh status bar.
    statusbar.print()
    epaper.pauseEpaper()
    for k, v in menu.items():
        epaper.writeText(row, "    " + str(v))
        row = row + 1
    epaper.unPauseEpaper()    
    time.sleep(0.1)
    epaper.clearArea(0, 20 + shift, 17, 295)
    draw = ImageDraw.Draw(epaper.epaperbuffer)
    draw.polygon(
        [
            (2, (menuitem * 20) + 2 + shift),
            (2, (menuitem * 20) + 18 + shift),
            (17, (menuitem * 20) + 10 + shift),
        ],
        fill=0,
    )
    draw.line((17, 20 + shift, 17, 295), fill=0, width=1)
    statusbar.print()         
    event_key.wait()
    event_key.clear()
    return selection


# Turn Leds off, beep, clear DGT Centaur Serial
# Initialise the epaper display - after which functions in epaper.py are available but you can also draw to the
# image epaper.epaperbuffer to change the screen.
board.ledsOff()
board.beep(board.SOUND_POWER_ON)
epaper.initEpaper(1)
board.clearSerial()
statusbar = epaper.statusBar()
statusbar.start()
update = centaur.UpdateSystem()
logging.debug("Setting checking for updates in 5 mins.")
threading.Timer(300, update.main).start()
# Subscribe to board events. First parameter is the function for key presses. The second is the function for
# field activity
board.subscribeEvents(keyPressed, None, timeout=900)


def show_welcome():
    global idle
    epaper.welcomeScreen()
    idle = True
    event_key.wait()
    event_key.clear()
    idle = False


show_welcome()
epaper.quickClear()


def get_lichess_client():
    logging.debug("get_lichess_client")
    import berserk
    import berserk.exceptions
    token = centaur.get_lichess_api()
    if not len(token):
        logging.error('lichess token not defined')
        raise ValueError('lichess token not defined')
    session = berserk.TokenSession(token)
    client = berserk.Client(session=session)
    # just to test if the token is a valid one
    try:
        who = client.account.get()
    except berserk.exceptions.ResponseError:
        logging.error('Lichess API error. Wrong token maybe?')
        raise
    return client


# Handle the menu structure
while True:    
    menu = {}
    if os.path.exists(centaur_software):
        centaur_item = {"Centaur": "DGT Centaur"}
        menu.update(centaur_item)
    menu.update({"pegasus": "DGT Pegasus"})
    if centaur.lichess_api:
        lichess_item = {"Lichess": "Lichess"}
        menu.update(lichess_item)
    if centaur.get_menuEngines() != "unchecked":
        menu.update({"Engines": "Engines"})
    if centaur.get_menuHandBrain() != "unchecked":
        menu.update({"HandBrain": "Hand + Brain"})
    if centaur.get_menu1v1Analysis() != "unchecked":
        menu.update({"1v1Analysis": "1v1 Analysis"})
    if centaur.get_menuEmulateEB() != "unchecked":
        menu.update({"EmulateEB": "e-Board"})
    if centaur.get_menuCast() != "unchecked":
        menu.update({"Cast": "Chromecast"})
    logging.debug("Checking for custom files")
    pyfiles = os.listdir("/home/pi")
    foundpyfiles = 0
    for pyfile in pyfiles:        
        if pyfile[-3:] == ".py" and pyfile != "firstboot.py":
            logging.debug("found custom files")
            foundpyfiles = 1
            break
    logging.debug("Custom file check complete")
    if foundpyfiles == 1:
        menu.update({"Custom": "Custom"})
    if centaur.get_menuSettings() != "unchecked":
        menu.update({"settings": "Settings"})
    if centaur.get_menuAbout() != "unchecked":
        menu.update({"About": "About"})                                
    result = doMenu(menu, "Main menu")
    # epaper.epd.init()
    # time.sleep(0.7)
    # epaper.clearArea(0,0 + shift,128,295)
    # time.sleep(1)
    if result == "BACK":
        board.beep(board.SOUND_POWER_OFF)
        show_welcome()
    if result == "Cast":
        epaper.loadingScreen()
        board.pauseEvents()
        statusbar.stop()
        os.system(
            str(sys.executable)
            + " "
            + str(pathlib.Path(__file__).parent.resolve())
            + "/../display/chromecast.py"
        )
        board.unPauseEvents()
        statusbar.start()
    if result == "Centaur":
        epaper.loadingScreen()
        #time.sleep(1)
        board.pauseEvents()
        statusbar.stop()
        board.ser.close()
        time.sleep(1)
        os.chdir("/home/pi/centaur")
        os.system("sudo ./centaur")
        # Once started we cannot return to DGTCentaurMods, we can kill that
        time.sleep(3)
        os.system("sudo systemctl stop DGTCentaurMods.service")
        sys.exit()
    if result == "pegasus":
        epaper.loadingScreen()
        statusbar.stop()
        board.pauseEvents()
        os.system(
            str(sys.executable)
            + " "
            + str(pathlib.Path(__file__).parent.resolve())
            + "/pegasus.py"
        )
        statusbar.start()
        board.unPauseEvents()
    if result == "EmulateEB":
        boardmenu = {
            "dgtclassic": "DGT REVII",
            "millennium": "Millennium",
        }
        result = doMenu(boardmenu, "e-Board")
        if result == "dgtclassic":
            epaper.loadingScreen()
            board.pauseEvents()
            statusbar.stop()
            os.system(
                "sudo "
                + str(sys.executable)
                + " "
                + str(pathlib.Path(__file__).parent.resolve())
                + "/eboard.py"
            )
            board.unPauseEvents()
            statusbar.start()
        if result == "millennium":
            epaper.loadingScreen()
            board.pauseEvents()
            statusbar.stop()
            os.system(
                "sudo "
                + str(sys.executable)
                + " "
                + str(pathlib.Path(__file__).parent.resolve())
                + "/millenium.py"
            )
            board.unPauseEvents()
            statusbar.start()
    if result == "1v1Analysis":
        epaper.loadingScreen()
        board.pauseEvents()
        statusbar.stop()
        os.system(
            "sudo "
            + str(sys.executable)
            + " "
            + str(pathlib.Path(__file__).parent.resolve())
            + "/1v1Analysis.py"
        )
        epaper.quickClear()
        board.unPauseEvents()
    if result == "settings":
        setmenu = {
            "WiFi": "Wifi Setup",
            "Pairing": "BT Pair",
            "Sound": "Sound",
            "LichessAPI": "Lichess API",
            "reverseshell": "Shell 7777",
            "update": "Update opts",            
            "Shutdown": "Shutdown",
            "Reboot": "Reboot",
        }
        topmenu = False
        while topmenu == False:
            result = doMenu(setmenu, "Settings")
            logging.debug(result)
            if result == "update":
                topmenu = False
                while topmenu == False:
                    updatemenu = {"status": "State: " + update.getStatus()}
                    package = "/tmp/dgtcentaurmods_armhf.deb"
                    if update.getStatus() == "enabled":
                        updatemenu.update(
                            {
                                "channel": "Chnl: " + update.getChannel(),
                                "policy": "Plcy: " + update.getPolicy(),
                            }
                        )
                    # Check for .deb files in the /home/pi folder that have been uploaded by webdav
                    updatemenu["lastrelease"] = "Last Release"
                    debfiles = os.listdir("/home/pi")
                    logging.debug("Check for deb files that system can update to")
                    for debfile in debfiles:        
                        if debfile[-4:] == ".deb" and debfile[:15] == "dgtcentaurmods_":
                            logging.debug("Found " + debfile)
                            updatemenu[debfile] = debfile[15:debfile.find("_",15)]                    
                    selection = ""
                    result = doMenu(updatemenu, "Update opts")
                    if result == "status":
                        result = doMenu(
                            {"enable": "Enable", "disable": "Disable"}, "Status"
                        )
                        logging.debug(result)
                        if result == "enable":
                            update.enable()
                        if result == "disable":
                            update.disable()
                            try:
                                os.remove(package)
                            except:
                                pass
                    if result == "channel":
                        result = doMenu({"stable": "Stable", "beta": "Beta"}, "Channel")
                        update.setChannel(result)
                    if result == "policy":
                        result = doMenu(
                            {"always": "Always", "revision": "Revisions"}, "Policy"
                        )
                        update.setPolicy(result)
                    if result == "lastrelease":
                        logging.debug("Last Release")
                        update_source = update.conf.read_value('update', 'source')
                        logging.debug(update_source)
                        url = 'https://raw.githubusercontent.com/{}/master/DGTCentaurMods/DEBIAN/versions'.format(update_source)                   
                        logging.debug(url)
                        ver = None
                        try:
                            with urllib.request.urlopen(url) as versions:
                                ver = json.loads(versions.read().decode())
                                logging.debug(ver)
                        except Exception as e:
                            logging.debug('!! Cannot download update info: ', e)
                        pass
                        if ver != None:
                            logging.debug(ver["stable"]["release"])
                            download_url = 'https://github.com/{}/releases/download/v{}/dgtcentaurmods_{}_armhf.deb'.format(update_source,ver["stable"]["release"],ver["stable"]["release"])
                            logging.debug(download_url)
                            try:
                                urllib.request.urlretrieve(download_url,'/tmp/dgtcentaurmods_armhf.deb')
                                logging.debug("downloaded to /tmp")
                                os.system("cp -f /home/pi/" + result + " /tmp/dgtcentaurmods_armhf.deb")
                                logging.debug("Starting update")
                                update.updateInstall()
                            except:
                                pass
                    if os.path.exists("/home/pi/" + result):
                        logging.debug("User selected .deb file. Doing update")
                        logging.debug("Copying .deb file to /tmp")
                        os.system("cp -f /home/pi/" + result + " /tmp/dgtcentaurmods_armhf.deb")
                        logging.debug("Starting update")
                        update.updateInstall()
                    if selection == "BACK":
                        # Trigger the update system to appply new settings
                        try:
                            os.remove(package)
                        except:
                            pass
                        finally:
                            threading.Thread(target=update.main, args=()).start()
                        topmenu = True
                        logging.debug("return to settings")
                        selection = ""
            topmenu = False
            if selection == "BACK":
                topmenu = True
                result = ""

            if result == "Sound":
                soundmenu = {"On": "On", "Off": "Off"}
                result = doMenu(soundmenu, "Sound")
                if result == "On":
                    centaur.set_sound("on")
                if result == "Off":
                    centaur.set_sound("off")
            if result == "WiFi":
                if network.check_network():
                    wifimenu = {"wpa2": "WPA2-PSK", "wps": "WPS Setup"}
                else:
                    wifimenu = {
                        "wpa2": "WPA2-PSK",
                        "wps": "WPS Setup",
                        "recover": "Recover wifi",
                    }
                if network.check_network():
                    cmd = (
                        'sudo sh -c "'
                        + str(pathlib.Path(__file__).parent.resolve())
                        + '/../scripts/wifi_backup.sh backup"'
                    )                    
                    centaur.shell_run(cmd)
                result = doMenu(wifimenu, "Wifi Setup")
                if result != "BACK":
                    if result == "wpa2":
                        epaper.loadingScreen()
                        os.system(
                            str(sys.executable)
                            + " "
                            + str(pathlib.Path(__file__).parent.resolve())
                            + "/../config/wifi.py"
                        )
                        board.unPauseEvents()
                    if result == "wps":
                        if network.check_network():
                            selection = ""
                            curmenu = None
                            IP = network.check_network()
                            epaper.clearScreen()
                            epaper.writeText(0, "Network is up.")
                            epaper.writeText(1, "Press OK to")
                            epaper.writeText(2, "disconnect")
                            epaper.writeText(4, IP)
                            timeout = time.time() + 15
                            while time.time() < timeout:
                                if selection == "BTNTICK":
                                    network.wps_disconnect_all()
                                    break
                                time.sleep(2)
                        else:
                            wpsMenu = {"connect": "Connect wifi"}
                            result = doMenu(wpsMenu, "WPS")
                            if result == "connect":
                                epaper.clearScreen()
                                epaper.writeText(0, "Press WPS button")
                                network.wps_connect()
                    if result == "recover":
                        selection = ""
                        cmd = (
                            'sudo sh -c "'
                            + str(pathlib.Path(__file__).parent.resolve())
                            + '/../scripts/wifi_backup.sh restore"'
                        )
                        centaur.shell_run(cmd)                    
                        timeout = time.time() + 20
                        epaper.clearScreen()
                        epaper.writeText(0, "Waiting for")
                        epaper.writeText(1, "network...")
                        while not network.check_network() and time.time() < timeout:
                            time.sleep(1)
                        if not network.check_network():
                            epaper.writeText(1, "Failed to restore...")
                            time.sleep(4)

            if result == "Pairing":
                board.pauseEvents()
                statusbar.stop()
                epaper.loadingScreen()
                os.system(
                    str(sys.executable)
                    + " "
                    + str(pathlib.Path(__file__).parent.resolve())
                    + "/../config/pair.py"
                )
                board.unPauseEvents()
                statusbar.start()
            if result == "LichessAPI":
                board.pauseEvents()
                statusbar.stop()
                epaper.loadingScreen()
                os.system(
                    str(sys.executable)
                    + " "
                    + str(pathlib.Path(__file__).parent.resolve())
                    + "/../config/lichesstoken.py"
                )
                board.unPauseEvents()
                statusbar.start()
            if result == "Shutdown":
                statusbar.stop()
                board.shutdown()
                input()
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
            if result == "reverseshell":
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("0.0.0.0", 7777))
                s.listen(1)
                conn, addr = s.accept()
                conn.send(b'With great power comes great responsibility! Use this if you\n')
                conn.send(b'can\'t get into ssh for some reason. Otherwise use ssh!\n')
                conn.send(b'\nBy using this you agree that a modified DGT Centaur Mods board\n')
                conn.send(b'is the best chessboard in the world.\n')
                conn.send(b'----------------------------------------------------------------------\n')                
                os.dup2(conn.fileno(),0)
                os.dup2(conn.fileno(),1)
                os.dup2(conn.fileno(),2)
                p=subprocess.call(["/bin/bash","-i"])
    if result == "Lichess":
        livemenu = {"Rated": "Rated", "Unrated": "Unrated", "Ongoing": "Ongoing", 'Challenges': 'Challenges'}
        result = doMenu(livemenu, "Lichess")
        logging.debug('menu active: lichess')
        if result != "BACK":
            if result == "Ongoing":
                logging.debug('menu active: Ongoing')
                client = get_lichess_client()
                ongoing_games = client.games.get_ongoing(10)
                ongoing_menu = {}
                logging.debug(f"{ongoing_menu}")
                for game in ongoing_games:
                    gameid = game["gameId"]
                    opponent = game['opponent']['id']
                    if game['color'] == 'white':
                        desc = f"{client.account.get()['username']} vs. {opponent}"
                    else:
                        desc = f" {opponent} vs. {client.account.get()['username']}"
                    ongoing_menu[gameid] = desc
                logging.debug(f"ongoing menu: {ongoing_menu}")
                if len(ongoing_menu) > 0:
                    result = doMenu(ongoing_menu, "Current games:")
                    if result != "BACK":
                        logging.debug(f"menu current games")
                        game_id = result
                        epaper.loadingScreen()
                        board.pauseEvents()
                        logging.debug(f"staring lichess")
                        os.system(f"{sys.executable} {pathlib.Path(__file__).parent.resolve()}"
                                  f"/../game/lichess.py Ongoing {game_id}"
                                  )
                        board.unPauseEvents()
                else:
                    logging.warning("No ongoing games!")
                    epaper.writeText(1, "No ongoing games!")
                    time.sleep(3)


            elif result == "Challenges":
                client = get_lichess_client()
                challenge_menu = {}
                # very ugly call, there is no adequate method in berserk's API,
                # see https://github.com/rhgrant10/berserk/blob/master/berserk/todo.md
                challenges = client._r.get('api/challenge')
                for challenge in challenges['in']:
                    challenge_menu[f"{challenge['id']}:in"] = f"in: {challenge['challenger']['id']}"
                for challenge in challenges['out']:
                    challenge_menu[f"{challenge['id']}:out"] = f"out: {challenge['destUser']['id']}"
                result = doMenu(challenge_menu, "Challenges")
                if result != "BACK":
                    logging.debug('menu active: Challenge')
                    game_id, challenge_direction = result.split(":")
                    epaper.loadingScreen()
                    board.pauseEvents()
                    logging.debug(f"staring lichess")
                    os.system(f"{sys.executable} {pathlib.Path(__file__).parent.resolve()}"
                              f"/../game/lichess.py Challenge {game_id} {challenge_direction}"
                              )
                    board.unPauseEvents()

            else:  # new Rated or Unrated
                if result == "Rated":
                    rated = True
                else:
                    assert result == "Unrated", "Wrong game type"  #nie można rzucać wyjątków, bo cała aplikacja się sypie
                    rated = False
                colormenu = {"random": "Random", "white": "White", "black": "Black"}
                result = doMenu(colormenu, "Color")
                if result != "BACK":
                    color = result
                    timemenu = {
                        "10 , 5": "10+5 minutes",
                        "15 , 10": "15+10 minutes",
                        "30 , 0": "30 minutes",
                        "30 , 20": "30+20 minutes",
                        "45 , 45": "45+45 minutes",
                        "60 , 20": "60+20 minutes",
                        "60 , 30": "60+30 minutes",
                        "90 , 30": "90+30 minutes",
                    }
                    result = doMenu(timemenu, "Time")

                    if result != "BACK":
                        # split time and increment '10 , 5' -> ['10', '5']
                        seek_time = result.split(",")
                        gtime = int(seek_time[0])
                        gincrement = int(seek_time[1])
                        epaper.loadingScreen()
                        board.pauseEvents()
                        os.system(f"{sys.executable} {pathlib.Path(__file__).parent.resolve()}/../game/lichess.py "
                                  f"New {gtime} {gincrement} {rated} {color}"
                                  )
                        board.unPauseEvents()
    if result == "Engines":
        enginemenu = {"stockfish": "Stockfish"}
        # Pick up the engines from the engines folder and build the menu
        enginepath = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
        enginefiles = os.listdir(enginepath)
        enginefiles = list(
            filter(lambda x: os.path.isfile(enginepath + x), os.listdir(enginepath))
        )        
        for f in enginefiles:
            fn = str(f)
            if "." not in fn:
                # If this file don't have an extension then it is an engine
                enginemenu[fn] = fn
        result = doMenu(enginemenu, "Engines")
        logging.debug("Engines")
        logging.debug(result)
        if result == "stockfish":
            sfmenu = {"white": "White", "black": "Black", "random": "Random"}
            color = doMenu(sfmenu, "Color")
            logging.debug(color)
            # Current game will launch the screen for the current
            if color != "BACK":
                ratingmenu = {
                    "2850": "Pure",
                    "1350": "1350 ELO",
                    "1500": "1500 ELO",
                    "1700": "1700 ELO",
                    "1800": "1800 ELO",
                    "2000": "2000 ELO",
                    "2200": "2200 ELO",
                    "2400": "2400 ELO",
                    "2600": "2600 ELO",
                }
                elo = doMenu(ratingmenu, "ELO")
                if elo != "BACK":
                    epaper.loadingScreen()
                    board.pauseEvents()
                    statusbar.stop()
                    os.system(
                        str(sys.executable)
                        + " "
                        + str(pathlib.Path(__file__).parent.resolve())
                        + "/../game/stockfish.py "
                        + color
                        + " "
                        + elo
                    )
                    board.unPauseEvents()
                    statusbar.start()
        else:
            if result != "BACK":
                # There are two options here. Either a file exists in the engines folder as enginename.uci which will give us menu options, or one doesn't and we run it as default
                enginefile = enginepath + result
                ucifile = enginepath + result + ".uci"
                cmenu = {"white": "White", "black": "Black", "random": "Random"}
                color = doMenu(cmenu, result)
                # Current game will launch the screen for the current
                if color != "BACK":
                    if os.path.exists(ucifile):
                        # Read the uci file and build a menu
                        config = configparser.ConfigParser()
                        config.read(ucifile)
                        logging.debug(config.sections())
                        smenu = {}
                        for sect in config.sections():
                            smenu[sect] = sect
                        sec = doMenu(smenu, result)
                        if sec != "BACK":
                            epaper.loadingScreen()
                            board.pauseEvents()
                            statusbar.stop()
                            logging.debug(
                                str(pathlib.Path(__file__).parent.resolve())
                                + "/../game/uci.py "
                                + color
                                + ' "'
                                + result
                                + '"'
                                + ' "'
                                + sec
                                + '"'
                            )
                            os.system(
                                str(sys.executable)
                                + " "
                                + str(pathlib.Path(__file__).parent.resolve())
                                + "/../game/uci.py "
                                + color
                                + ' "'
                                + result
                                + '"'
                                + ' "'
                                + sec
                                + '"'
                            )
                            board.unPauseEvents()
                            epaper.quickClear()
                            statusbar.start()
                    else:
                        # With no uci file we just call the engine
                        epaper.loadingScreen()
                        board.pauseEvents()
                        statusbar.stop()
                        logging.debug(
                            str(pathlib.Path(__file__).parent.resolve())
                            + "/../game/uci.py "
                            + color
                            + ' "'
                            + result
                            + '"'
                        )
                        os.system(
                            str(sys.executable)
                            + " "
                            + str(pathlib.Path(__file__).parent.resolve())
                            + "/../game/uci.py "
                            + color
                            + ' "'
                            + result
                            + '"'
                        )
                        board.unPauseEvents()
                        epaper.quickClear()
                        statusbar.start()
    if result == "HandBrain":
        # Pick up the engines from the engines folder and build the menu
        enginemenu = {}
        enginepath = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
        enginefiles = os.listdir(enginepath)
        enginefiles = list(
            filter(lambda x: os.path.isfile(enginepath + x), os.listdir(enginepath))
        )
        logging.debug(enginefiles)
        for f in enginefiles:
            fn = str(f)
            if ".uci" not in fn:
                # If this file is not .uci then assume it is an engine
                enginemenu[fn] = fn
        result = doMenu(enginemenu, "Engines")
        logging.debug(result)
        if result != "BACK":
            # There are two options here. Either a file exists in the engines folder as enginename.uci which will give us menu options, or one doesn't and we run it as default
            enginefile = enginepath + result
            ucifile = enginepath + result + ".uci"
            cmenu = {"white": "White", "black": "Black", "random": "Random"}
            color = doMenu(cmenu, result)
            # Current game will launch the screen for the current
            if color != "BACK":
                if os.path.exists(ucifile):
                    # Read the uci file and build a menu
                    config = configparser.ConfigParser()
                    config.read(ucifile)
                    logging.debug(config.sections())
                    smenu = {}
                    for sect in config.sections():
                        smenu[sect] = sect
                    sec = doMenu(smenu, result)
                    if sec != "BACK":
                        epaper.loadingScreen()
                        board.pauseEvents()
                        statusbar.stop()
                        logging.debug(
                            str(pathlib.Path(__file__).parent.resolve())
                            + "/../game/uci.py "
                            + color
                            + ' "'
                            + result
                            + '"'
                            + ' "'
                            + sec
                            + '"'
                        )
                        os.system(
                            str(sys.executable)
                            + " "
                            + str(pathlib.Path(__file__).parent.resolve())
                            + "/../game/handbrain.py "
                            + color
                            + ' "'
                            + result
                            + '"'
                            + ' "'
                            + sec
                            + '"'
                        )
                        board.unPauseEvents()
                        statusbar.start()
                else:
                    # With no uci file we just call the engine
                    epaper.loadingScreen()
                    board.pauseEvents()
                    statusbar.stop()
                    logging.debug(
                        str(pathlib.Path(__file__).parent.resolve())
                        + "/../game/uci.py "
                        + color
                        + ' "'
                        + result
                        + '"'
                    )
                    os.system(
                        str(sys.executable)
                        + " "
                        + str(pathlib.Path(__file__).parent.resolve())
                        + "/../game/handbrain.py "
                        + color
                        + ' "'
                        + result
                        + '"'
                    )
                    board.unPauseEvents()
                    statusbar.start()
    if result == "Custom":
        pyfiles = os.listdir("/home/pi")
        menuitems = {}
        for pyfile in pyfiles:        
            if pyfile[-3:] == ".py" and pyfile != "firstboot.py":                
                menuitems[pyfile] = pyfile
        result = doMenu(menuitems,"Custom Scripts")
        if result.find("..") < 0:
            logging.debug("Running custom file: " + result)
            os.system("python /home/pi/" + result)

    if result == "About" or result == "BTNHELP":
        selection = ""
        epaper.clearScreen()
        statusbar.print()
        version = os.popen(
            "dpkg -l | grep dgtcentaurmods | tr -s ' ' | cut -d' ' -f3"
        ).read()
        epaper.writeText(1, "Get support:")
        epaper.writeText(9, "DGTCentaur")
        epaper.writeText(10, "      Mods")
        epaper.writeText(11, "Ver:" + version)        
        qr = Image.open(AssetManager.get_resource_path("qr-support.png"))
        qr = qr.resize((128, 128))
        epaper.epaperbuffer.paste(qr, (0, 42))
        timeout = time.time() + 15
        while selection == "" and time.time() < timeout:
            if selection == "BTNTICK" or selection == "BTNBACK":
                break
        epaper.clearScreen()        
