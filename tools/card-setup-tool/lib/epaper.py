# Control the ePaper display of the DGT Centaur
#
# This method uses a thread to monitor for changes to an image
# Then any alterations to the image will show on the epaper
# You can either use the image functions in this file or modify epaper.epaperbuffer directly.
#
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

from lib import centaur
from lib import epd2in9d

import time, sched, os
from PIL import Image, ImageDraw, ImageFont
import pathlib
import threading
import hashlib

font18 = ImageFont.truetype("lib/font/Font.ttc", 18)
fixedfont = ImageFont.truetype("lib/font/fixed_01.ttf")
# Screenbuffer is what we want to display on the screen
epaperbuffer = Image.new('1', (128, 296), 255) # You can also use pillow to directly change this image
lastepaperhash = 0
epaperprocesschange = 1
epd = epd2in9d.EPD()
epaperUpd = ""
kill = 0
epapermode = 0
lastepaperbytes = bytearray(b'')
first = 1
event_refresh = threading.Event()
screeninverted = 0

def epaperUpdate():
    # This is used as a thread to update the e-paper if the image has changed
    global epaperbuffer
    global lastepaperhash
    global epaperprocesschange
    global kill
    global epapermode
    global lastepaperbytes
    global first
    global event_refresh
    global screeninverted
    print("started epaper update thread")
    epd.display(epd.getbuffer(epaperbuffer))
    time.sleep(1)
    print("epaper init image sent")
    while True and kill == 0:
        im = epaperbuffer.copy()
        im2 = im.copy()
        if epaperprocesschange == 1:
            tepaperbytes = im.tobytes()
        if lastepaperbytes != tepaperbytes and epaperprocesschange == 1:
            filename = "lib/epaper.jpg"
            epaperbuffer.save(filename)
            if screeninverted == 0:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            if epapermode == 0 or first == 1:
                epd.DisplayPartial(epd.getbuffer(im))
                first = 0
            else:
                rs = 0
                re = 295
                for x in range(0, len(tepaperbytes)):
                    if lastepaperbytes[x] != tepaperbytes[x]:
                        rs = (x // 16) - 1
                        break;
                for x in range(len(tepaperbytes) - 1, 0, -1):
                    if lastepaperbytes[x] != tepaperbytes[x]:
                        re = (x // 16) + 1
                        break;
                if rs < 0:
                    rs = 0
                if re > 295:
                    re = 295
                if rs >= re:
                    rs = 0
                    re = 295
                bb = im2.crop((0, rs + 1, 128, re))
                bb = bb.transpose(Image.FLIP_TOP_BOTTOM)
                bb = bb.transpose(Image.FLIP_LEFT_RIGHT)
                epd.DisplayRegion(296 - re, 295 - rs, epd.getbuffer(bb))
            lastepaperbytes = tepaperbytes
            event_refresh.set()
        time.sleep(0.2)

def refresh():
    # Just waits for a refresh
    event_refresh.clear()
    event_refresh.wait()
    event_refresh.clear()


def initEpaper(mode = 0):
    # Set the screen to a known start state and start the epaperUpdate thread
    global epaperbuffer
    global epaperUpd
    global epapermode
    epapermode = mode
    epaperbuffer = Image.new('1', (128, 296), 255)
    print("init epaper")
    epd.init()
    time.sleep(1)
    epd.Clear(0xff)
    time.sleep(2)
    epaperUpd = threading.Thread(target=epaperUpdate, args=())
    epaperUpd.daemon = True
    epaperUpd.start()

def pauseEpaper():
    # Pause epaper updates (for example if you know you will be making a lot of changes in quick succession
    global epaperprocesschange
    time.sleep(0.3)
    epaperprocesschange = 0
    time.sleep(0.3)

def unPauseEpaper():
    # Unpause previously paused epaper
    global epaperprocesschange
    epaperprocesschange = 1

def stopEpaper():
    # Stop the epaper
    global lastepaperhash
    global lastepaperbytes
    global epaperbuffer
    global kill
    filename = "lib/img/logo_mods_screen.jpg"
    lg = Image.open(filename)
    lgs = Image.new('1', (128, 296), 255)
    lgs.paste(lg,(0,0))
    qrfile = "lib/img/qr-support.png"
    qr = Image.open(qrfile)
    qr = qr.resize((128,128))
    lgs.paste(qr,(0,160))
    epaperbuffer = lgs.copy()
    time.sleep(3)
    kill = 1
    time.sleep(2)
    epd.sleep()

def killEpaper():
    global kill
    kill = 1

def writeText(row,txt):
    # Write Text on a give line number
    global epaperbuffer
    nimage = epaperbuffer.copy()
    image = Image.new('1', (128, 20), 255)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), txt, font=fixedfont, fill=0)
    nimage.paste(image, (0, (row * 20)))
    epaperbuffer = nimage.copy()

def writeMenuTitle(title):
    # Write Text on a give line number
    global epaperbuffer
    nimage = epaperbuffer.copy()
    image = Image.new('1', (128, 20), 0)
    draw = ImageDraw.Draw(image)
    draw.text((4, -2), title, font=font18, fill=255)
    nimage.paste(image, (0, 20))
    epaperbuffer = nimage.copy()

def drawRectangle(x1, y1, x2, y2, fill, outline):
    # Draw a rectangle
    global epaperbuffer
    draw = ImageDraw.Draw(epaperbuffer)
    draw.rectangle([(x1, y1), (x2, y2)], fill=fill, outline=outline)

def clearArea(x1, y1, x2, y2):
    # Clears an area of the screen. In fact just draws a white rectangle
    drawRectangle(x1,y1,x2,y2,255,255)

def clearScreen():
    # Set the ePaper back to white
    global epaperbuffer
    global event_refresh
    global first
    #epaperbuffer = Image.new('1', (128, 296), 255)
    draw = ImageDraw.Draw(epaperbuffer)
    draw.rectangle([(0, 0), (128, 296)], fill=255, outline=255)
    first = 1


class statusBar():
    def __init__(self):
        return

    def build(self):
    # This currently onlt shows the time but we can prepare it as an Image to
    # put it on top of the screen
        self.clock = time.strftime("%H:%M")
        self.bar = self.clock+"      "+ centaur.temp()
        return self.bar

    def display(self):
        while self.is_running:
            bar = self.build()
            writeText(0,bar)
            time.sleep(30)

    def print(self):
    #Get the latest status bar if needed.
        #if self.is_running:
        bar = self.build()
        writeText(0,bar)
        return

    def init(self):
        print("Starting status bar update thread")
        self.statusbar = threading.Thread(target=self.display, args=())
        self.statusbar.daemon = True
        self.statusbar.start()

    def start(self):
        self.is_running = True
        self.init()

    def stop(self):
        print("Kill status bar thread")
        self.is_running = False


