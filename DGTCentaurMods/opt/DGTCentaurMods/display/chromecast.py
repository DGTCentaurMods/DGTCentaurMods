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

from DGTCentaurMods.board import board, network
from DGTCentaurMods.display import epaper
from PIL import Image, ImageDraw, ImageFont
import time
import pathlib
import os
import sys
import pychromecast
from random import random

chromecasts = pychromecast.get_chromecasts()

curmenu = []
menuitem = 0
selection = ""
def keyPressed(id):
    # This function receives key presses
    global menuitem
    global curmenu
    global selection
    board.beep(board.SOUND_GENERAL)
    if id == board.BTNDOWN:
        menuitem = menuitem + 1
    if id == board.BTNUP:
        menuitem = menuitem - 1
    if id == board.BTNTICK:
        c = 1
        r = ""
        for v in curmenu:
            if (c == menuitem):
                selection = c
                menuitem = 1
                return
            c = c + 1
    if id == board.BTNBACK:
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
        board.beep(board.SOUND_GENERAL)
        menuitem = (id * -1) - 23
        c = 1
        r = ""
        for v in curmenu:
            if (c == menuitem):
                selection = c
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
    board.pauseEvents()
    res = board.getBoardState()
    board.unPauseEvents()
    if res[32] == 0 and res[33] == 0 and res[34] == 0 and res[35] == 0 and res[36]==0 and res[37] == 0 and res[38] == 0 and res[39] == 0:
        # If the 4th rank is empty then enable quick select mode. Then we can choose a menu option by placing and releasing a piece
        quickselect = 1
    row = 1
    for v in menu:
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
os.system("ps -ef | grep 'cchandler.py' | grep -v grep | awk '{print $2}' | xargs -r kill -9")
board.ledsOff()
board.clearSerial()
epaper.initEpaper()
# Subscribe to board events. First parameter is the function for key presses. The second is the function for
# field activity
board.subscribeEvents(keyPressed, fieldActivity)

for cc in chromecasts[0]:
    curmenu.append(cc.device.friendly_name)

# Let the user choose the chromecast
result = doMenu(curmenu)

if result == "BACK":
    sys.exit()

result = result - 1

ccname = chromecasts[0][result].device.friendly_name

os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + '/../display/cchandler.py "' + ccname + '" &')
