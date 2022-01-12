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

from DGTCentaurMods.display import epd2in9d
import time
from PIL import Image, ImageDraw, ImageFont
import pathlib
import threading
import hashlib

font18 = ImageFont.truetype(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/Font.ttc", 18)
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
    time.sleep(6)
    print("epaper init image sent")
    while True and kill == 0:
        im = epaperbuffer.copy()
        im2 = im.copy()
        if epaperprocesschange == 1:
            tepaperbytes = im.tobytes()
        if lastepaperbytes != tepaperbytes and epaperprocesschange == 1:
            filename = str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg"
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
    filename = str(pathlib.Path(__file__).parent.resolve()) + "/../resources/logo_mods_screen.jpg"
    lg = Image.open(filename)
    lgs = Image.new('1', (128, 296), 255)
    lgs.paste(lg,(0,0))
    qrfile = str(pathlib.Path(__file__).parent.resolve()) + "/../resources/qr-support.png"
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
    draw.text((0, 0), txt, font=font18, fill=0)
    nimage.paste(image, (0, (row * 20)))
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

def drawBoard(pieces, startrow=2):
    global epaperbuffer
    chessfont = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/chesssprites.bmp")
    for x in range(0,64):
        pos = (x - 63) * -1
        row = ((startrow * 20) + 8) + (16 * (pos // 8))
        col = (x % 8) * 16
        px = 0
        r = x // 8
        c = x % 8
        py = 0
        if (r // 2 == r / 2 and c // 2 == c / 2):
            py = py + 16
        if (r //2 != r / 2 and c // 2 != c / 2):
            py = py + 16
        if pieces[x] == "P":
            px = 16
        if pieces[x] == "R":
            px = 32
        if pieces[x] == "N":
            px = 48
        if pieces[x] == "B":
            px = 64
        if pieces[x] == "Q":
            px = 80
        if pieces[x] == "K":
            px = 96
        if pieces[x] == "p":
            px = 112
        if pieces[x] == "r":
            px = 128
        if pieces[x] == "n":
            px = 144
        if pieces[x] == "b":
            px = 160
        if pieces[x] == "q":
            px = 176
        if pieces[x] == "k":
            px = 192
        piece = chessfont.crop((px, py, px+16, py+16))
        epaperbuffer.paste(piece,(col, row))

def drawFen(fen, startrow=2):
    # As drawboard but draws a fen
    curfen = fen
    curfen = curfen.replace("/", "")
    curfen = curfen.replace("1", " ")
    curfen = curfen.replace("2", "  ")
    curfen = curfen.replace("3", "   ")
    curfen = curfen.replace("4", "    ")
    curfen = curfen.replace("5", "     ")
    curfen = curfen.replace("6", "      ")
    curfen = curfen.replace("7", "       ")
    curfen = curfen.replace("8", "        ")
    nfen = ""
    for a in range(8,0,-1):
        for b in range(0,8):
            nfen = nfen + curfen[((a-1)*8)+b]
    drawBoard(nfen, startrow)

def promotionOptions(row):
    # Draws the promotion options to the screen buffer
    global epaperbuffer
    print("drawing promotion options")
    offset = row * 20
    draw = ImageDraw.Draw(epaperbuffer)
    draw.text((0, offset+0), "    Q    R    N    B", font=font18, fill=0)
    draw.polygon([(2, offset+18), (18, offset+18), (10, offset+3)], fill=0)
    draw.polygon([(35, offset+3), (51, offset+3), (43, offset+18)], fill=0)
    o = 66
    draw.line((0+o,offset+16,16+o,offset+16), fill=0, width=5)
    draw.line((14+o,offset+16,14+o,offset+5), fill=0, width=5)
    draw.line((16+o,offset+6,4+o,offset+6), fill=0, width=5)
    draw.polygon([(8+o, offset+2), (8+o, offset+10), (0+o, offset+6)], fill=0)
    o = 97
    draw.line((6+o,offset+16,16+o,offset+4), fill=0, width=5)
    draw.line((2+o,offset+10, 8+o,offset+16), fill=0, width=5)

def resignDrawMenu(row):
    # Draws draw or resign options to the screen buffer
    global epaperbuffer
    offset = row * 20
    draw = ImageDraw.Draw(epaperbuffer)
    draw.text((0, offset + 0), "    DRW    RESI", font=font18, fill=0)
    draw.polygon([(2, offset + 18), (18, offset + 18), (10, offset + 3)], fill=0)
    draw.polygon([(35+25, offset + 3), (51+25, offset + 3), (43+25, offset + 18)], fill=0)
