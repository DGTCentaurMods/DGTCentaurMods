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
    epaper.epapermode = 0
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
                event_key.set()
                menuitem = 1
                return
            c = c + 1
    if id == board.BTNBACK:
        selection = "BACK"
        #epaper.epd.Clear(0xff)
        #time.sleep(2)
        event_key.set()
        return
    if id == board.BTNHELP:
        selection = "BTNHELP"
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
    epaper.epapermode = 0
    selection = ""
    curmenu = menu
    # Display the given menu
    menuitem = 1
    quickselect = 0
    board.pauseEvents()
    res = board.getBoardState()
    board.unPauseEvents()
    epaper.pauseEpaper()
    # If 3rd and 4th ranks are empty then enable quick select by placing and releasing a piece
    if res[32] == 0 and res[33] == 0 and res[34] == 0 and res[35] == 0 and res[36] == 0 and res[37] == 0 and res[38] == 0 and res[39] == 0:
        if res[24] == 0 and res[25] == 0 and res[26] == 0 and res[27] == 0 and res[28] == 0 and res[29] == 0 and res[30] == 0 and res[31] == 0:
            quickselect = 1
    row = 1
    #Print a fresh status bar.
    statusbar.print()
    for k, v in menu.items():
        epaper.writeText(row,"    " + str(v))
        row = row + 1
    for x in range(1,16):
        epaper.writeText(row,"                         ")
        row = row + 1
    epaper.clearArea(0,0,17,295)
    draw = ImageDraw.Draw(epaper.epaperbuffer)
    draw.polygon([(2, (menuitem * 20) + 2), (2, (menuitem * 20) + 18),
                  (17, (menuitem * 20) + 10)], fill=0)
    draw.line((17,20,17,295), fill=0, width=1)
    print("drawn")
    epaper.unPauseEpaper()
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
statusbar = epaper.statusBar()
statusbar.start()
# Subscribe to board events. First parameter is the function for key presses. The second is the function for
# field activity
board.subscribeEvents(keyPressed, fieldActivity)


# Handle the menu structure
while True:
    menu = {}
    if os.path.exists(centaur_software):
        centaur_item = {'Centaur': 'DGT Centaur'}
        menu.update(centaur_item)
    menu.update({'pegasus' : 'DGT Pegasus'})
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
    #epaper.epd.init()
    #time.sleep(0.7)
    #epaper.clearArea(0,0,128,295)
    #time.sleep(1)
    if result == "BACK":
        board.beep(board.SOUND_POWER_OFF)
    if result == "Cast":
        exec(open("menu/items/Cast").read())
    if result == "Centaur":
        exec(open("menu/items/Centaur").read())
    if result == "pegasus":
        exec(open("menu/items/pegasus").read())
    if result == "EmulateEB":
        exec(open("menu/items/EmulateEB").read())
    if result == "settings":
        exec(open("menu/items/settings").read())
    if result == "Lichess":
        exec(open("menu/items/Lichess").read())
    if result == "Engines":
        exec(open("menu/items/Engines").read())
    if result == "Support" or result == "BTNHELP":
        exec(open("menu/items/Support").read())


