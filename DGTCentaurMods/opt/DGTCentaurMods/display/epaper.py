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

from DGTCentaurMods.board import centaur,board
from DGTCentaurMods.display import epd2in9d
from DGTCentaurMods.display.epaper_driver import epaperDriver
from DGTCentaurMods.display.ui_components import AssetManager
import os, time
from PIL import Image, ImageDraw, ImageFont
import pathlib
import threading
import logging

try:
    logging.basicConfig(level=logging.DEBUG, filename="/home/pi/debug.log",filemode="w")
except:
    logging.basicConfig(level=logging.DEBUG)

driver = epaperDriver()

font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
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
    global screensleep
    global sleepcount
    logging.debug("started epaper update thread")    
    driver.display(epaperbuffer)    
    logging.debug("epaper init image sent")
    tepaperbytes = ""
    screensleep = 0
    sleepcount = 0
    while True and kill == 0:
        im = epaperbuffer.copy()
        im2 = im.copy()
        if epaperprocesschange == 1:
            tepaperbytes = im.tobytes()
        if lastepaperbytes != tepaperbytes and epaperprocesschange == 1:
            sleepcount = 0
            if screensleep == 1:
                driver.reset()
                screensleep = 0
            filename = str(AssetManager.get_resource_path("epaper.jpg"))
            epaperbuffer.save(filename)
            if screeninverted == 0:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.transpose(Image.FLIP_LEFT_RIGHT)                        
            if epapermode == 0 or first == 1:                
                driver.DisplayPartial(im)
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
                driver.DisplayRegion(296 - re, 295 - rs, bb)                             
            lastepaperbytes = tepaperbytes
            #event_refresh.set() 
        sleepcount = sleepcount + 1
        if sleepcount == 15000 and screensleep == 0:
            screensleep = 1
            driver.sleepDisplay()       
        time.sleep(0.1)

def refresh():
    # Just waits for a refresh. Deprecated
    return


def loadingScreen():
    global epaperbuffer
    statusBar().print()
    filename = str(AssetManager.get_resource_path("logo_mods_screen.jpg"))
    lg = Image.open(filename)
    epaperbuffer.paste(lg,(0,20))
    writeText(10,'     Loading')
    logging.debug('Display loading screen')
    

def welcomeScreen():
    global epaperbuffer
    statusBar().print()
    filename = str(AssetManager.get_resource_path("logo_mods_screen.jpg"))
    lg = Image.open(filename)
    epaperbuffer.paste(lg,(0,20))
    writeText(10,'     Press')
    writeText(11,'      to start')
    draw = ImageDraw.Draw(epaperbuffer)
    # Tick sign location
    x,y = 75,200
    draw.line((6+x,y+16,16+x,y+4), fill=0, width=5)
    draw.line((2+x,y+10, 8+x,y+16), fill=0, width=5)


def standbyScreen(show):
    global epaperbuffer
    f = '/tmp/epapersave.bmp'
    if show:
        logging.debug('Saving buffer')
        epaperbuffer.save(f)
        statusBar().print()
        
        filename = str(AssetManager.get_resource_path("logo_mods_screen.jpg"))
        lg = Image.open(filename)
        epaperbuffer.paste(lg,(0,20))
        writeText(10,'   Press [>||]')
        writeText(11,'   to power on')
        
        if epaperprocesschange == 0:
            # Assume in partial mode
            drawImagePartial(0,0,epaperbuffer.crop((0,0,128,292)))

    if not show:
        logging.debug('Restore buffer')
        restore = Image.open(f)
        epaperbuffer.paste(restore,(0,0))
        if epaperprocesschange == 0:
            # Assume in partial mode
            drawImagePartial(0,0,epaperbuffer.crop((0,0,128,292)))
        os.remove(f)


def initEpaper(mode = 0):
    # Set the screen to a known start state and start the epaperUpdate thread
    global epaperbuffer
    global epaperUpd
    global epapermode    
    epapermode = mode
    epaperbuffer = Image.new('1', (128, 296), 255)
    logging.debug("init epaper")
    driver.reset()
    driver.init()      
    epaperUpd = threading.Thread(target=epaperUpdate, args=())
    epaperUpd.daemon = True
    epaperUpd.start()

def pauseEpaper():
    # Pause epaper updates (for example if you know you will be making a lot of changes in quick succession
    global epaperprocesschange
    #time.sleep(0.3)
    epaperprocesschange = 0
    #time.sleep(0.3)

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
    filename = str(AssetManager.get_resource_path("logo_mods_screen.jpg"))
    lg = Image.open(filename)
    lgs = Image.new('1', (128, 296), 255)
    lgs.paste(lg,(0,0))
    qrfile = str(AssetManger.get_resource_path("qr-support.png"))
    qr = Image.open(qrfile)
    qr = qr.resize((128,128))
    lgs.paste(qr,(0,160))
    epaperbuffer = lgs.copy()
    time.sleep(3)
    kill = 1
    time.sleep(2)
    driver.sleepDisplay()

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
    clearArea(0, (row * 20), 127, (row * 20) + 20)
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
    pauseEpaper()
    draw = ImageDraw.Draw(epaperbuffer)
    draw.rectangle([(0, 0), (128, 296)], fill=255, outline=255)
    driver.DisplayRegion(0, 295, epaperbuffer)
    driver.clear()
    first = 0    
    unPauseEpaper()

def drawBoard(pieces, startrow=2):         
    global epaperbuffer
    draw = ImageDraw.Draw(epaperbuffer)
    chessfont = Image.open(AssetManager.get_resource_path("chesssprites.bmp"))
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
    startpoint = ((startrow * 20) + 8)
    draw.rectangle([(0, startpoint),(127, startpoint + 127)], fill = None, outline='black')

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
    logging.debug("drawing promotion options")
    global epaperprocesschange
    font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
    writeText(13, "                    ")
    if epaperprocesschange == 1:    
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
    else:
        timage = Image.new('1', (128, 20), 255)
        draw = ImageDraw.Draw(timage)
        font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
        draw.text((0, 0), "    Q    R    N    B", font=font18, fill=0)      
        offset = 0
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
        logging.debug("drawing promotion options")
        drawImagePartial(0, 270, timage)
        logging.debug("drawn")

def resignDrawMenu(row):
    # Draws draw or resign options to the screen buffer
    global epaperbuffer
    global epaperprocesschange
    global font18
    if epaperprocesschange == 1:
        offset = row * 20
        draw = ImageDraw.Draw(epaperbuffer)
        draw.text((0, offset + 0), "    DRW    RESI", font=font18, fill=0)
        draw.polygon([(2, offset + 18), (18, offset + 18), (10, offset + 3)], fill=0)
        draw.polygon([(35+25, offset + 3), (51+25, offset + 3), (43+25, offset + 18)], fill=0)
    else:
        # If epaperprocesschange is 0 then assume that the app calling is using the new partial display functions
        timage = Image.new('1', (128, 20), 255)
        draw = ImageDraw.Draw(timage)
        font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
        draw.text((0, 0), "    DRW    RESI", font=font18, fill=0)
        draw.polygon([(2, 18), (18, 18), (10, 3)], fill=0)
        draw.polygon([(35+25, 3), (51+25, 3), (43+25, 18)], fill=0)
        drawImagePartial(0, 271, timage)
    
def quickClear():
    # Assumes the screen is in partial mode and makes it white    
    driver.clear()    
    
def drawWindow(x, y, w, data):
    # Calling this function assumes the screen is already initialised
    # if using epaper.py, also pauseEpaper() should have been run
    # x is a value 0 - 15 , representing the column that the first data byte represents
    # y is a value 0 - 291, representing the row that the first data byte starts on
    # w is a width value in bytes (e.g. 1 = 8 pixels, 2 = 16 pixels represented by 2 bytes, etc)
    # data holds the bytes to write to the screen and the epaper buffer

    # First take care of the epaperbuffer (the image goes to the web view for example)
    global epaperbuffer
    dxoff = x * 8
    dyoff = y
    dw = w
    tw = 0
    for i in range(0, len(data)):
        # Loop through each of the bytes
        if data[i] & 128 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8),dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8),dyoff),0)
        if data[i] & 64 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 1,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 1,dyoff),0)
        if data[i] & 32 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 2,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 2,dyoff),0)
        if data[i] & 16 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 3,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 3,dyoff),0)
        if data[i] & 8 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 4,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 4,dyoff),0)
        if data[i] & 4 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 5,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 5,dyoff),0)
        if data[i] & 2 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 6,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 6,dyoff),0)
        if data[i] & 1 > 0:
            epaperbuffer.putpixel((dxoff + (tw*8) + 7,dyoff),255)
        else:
            epaperbuffer.putpixel((dxoff + (tw*8) + 7,dyoff),0)
        tw = tw + 1
        if tw >= dw:
            tw = 0
            dyoff = dyoff + 1
    filename = str(AssetManger.get_resource_path("epaper.jpg"))
    epaperbuffer.save(filename)    

def drawImagePartial(x, y, img):
    # For backwards compatibility we just paste into the image here
    # the epaper code will take care of the partial drawing
    #width, height = img.size
    #drawWindow(x,y,width//8,list(img.tobytes()))
    epaperbuffer.paste(img,(x,y))

def drawBatteryIndicator():
    batteryindicator = "battery1"
    if board.batterylevel >= 6:
        batteryindicator = "battery2"
    if board.batterylevel >= 12:
        batteryindicator = "battery3"
    if board.batterylevel >= 18:
        batteryindicator = "battery4"            
    if board.chargerconnected > 0:
        batteryindicator = "batteryc"
        if board.batterylevel == 20:
            batteryindicator = "batterycf"    
    if board.batterylevel >= 0:
        img = Image.open(AssetManager.get_resource_path(batteryindicator + ".bmp"))
        epaperbuffer.paste(img,(98, 2))        
        #drawImagePartial(13,0,img)     

class statusBar():
    def __init__(self):
        return

    def build(self):
    # This currently onlt shows the time but we can prepare it as an Image to
    # put it on top of the screen
        self.clock = time.strftime("%H:%M")
        self.bar = self.clock
        #self.bar = self.clock+"      "+board.temp()
        #self.bar = self.clock+"   " + str(board.chargerconnected) + "   " + str(board.batterylevel)            
        return self.bar          

    def display(self):
        while self.is_running:
            bar = self.build()
            writeText(0,bar)
            drawBatteryIndicator()
            time.sleep(30)

    def print(self):
    #Get the latest status bar if needed.
        #if self.is_running:
        bar = self.build()
        writeText(0,bar)
        drawBatteryIndicator()
        return

    def init(self):
        logging.debug("Starting status bar update thread")
        self.statusbar = threading.Thread(target=self.display, args=())
        self.statusbar.daemon = True
        self.statusbar.start()

    def start(self):
        self.is_running = True
        self.init()

    def stop(self):
        logging.debug("Kill status bar thread")
        self.is_running = False


class MenuDraw:
    def __init__(self):
        self.statusbar = statusBar()


    def draw_page(self, title, items):
        logging.debug('-------------')
        logging.debug(title)
        logging.debug('-------------')
        global epaperbuffer
        draw = ImageDraw.Draw(epaperbuffer)
        draw.rectangle([(0, 0), (128, 296)], fill=255, outline=255)
        writeMenuTitle(title)
        row = 2
        for item in items:
            writeText(row, "  " + item)
            logging.debug(item)
            row += 1
        self.statusbar.print()
        # draw epaperbuffer to the screen
        im = epaperbuffer.copy()
        if screeninverted == 0:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        bytes = im.tobytes()
        filename = str(AssetManager.get_resource_path("epaper.jpg"))
        epaperbuffer.save(filename)
        epd.send_command(0x91)
        epd.send_command(0x90)
        epd.send_data(0)
        epd.send_data(127)
        epd.send_data(0)
        epd.send_data(0)
        epd.send_data(1)
        epd.send_data(35)
        epd.send_command(0x10)
        for i in range(0, 4672):
            epd.send_data(bytes[i] ^ 255)
        epd.send_command(0x13)
        for i in range(0, 4672):
            epd.send_data(bytes[i])
        epd.send_command(0x12)
        time.sleep(0.5)


    def highlight(self, index, rollaround = 0):
        if rollaround == 1:
            epd.send_command(0x91)
            epd.send_command(0x90)
            epd.send_data(120)
            epd.send_data(120+5)
            epd.send_data(0)
            epd.send_data(0)
            epd.send_data(0)
            epd.send_data(252)
            epd.send_command(0x28)
            epd.send_command(0x10)
            for i in range(0, 252):
                epd.send_data(0x00)
            epd.send_command(0x13)
            for i in range(0, 252):
                epd.send_data(0xFF)
            epd.send_command(0x12) 
            time.sleep(0.3)
        pos = 296 - (78 + (index * 20))
        draw = ImageDraw.Draw(epaperbuffer)
        draw.rectangle([(0, 40), (8, 191)], fill = 255, outline = 255)
        draw.rectangle([(2,((index + 2) * 20) + 5), (8, ((index+2) * 20) + 14)], fill = 0, outline = 0)
        filename = str(AssetManger.get_resource_path("epaper.jpg"))
        epaperbuffer.save(filename)
        epd.send_command(0x91) # Enter partial mode
        epd.send_command(0x90) # Set resolution
        epd.send_data(120) #x start
        epd.send_data(120+5) #x end
        epd.send_data(0) #y start high
        epd.send_data(pos) #y start low
        pos = pos + 23 + 8 + 20
        if index == 0:
            pos = pos - 20
        epd.send_data(pos//256) #y end high
        epd.send_data((pos % 256))  # y end low
        epd.send_command(0x28) # Send data
        epd.send_command(0x10) # buffer
        for i in range(0, 23):
            epd.send_data(0x00)
        for i in range(0, 8):
            epd.send_data(0xFF)
        if index > 0:
            for i in range(0, 21):
                epd.send_data(0x00)
        epd.send_command(0x13) # buffer
        for i in range(0, 23):
            epd.send_data(0xFF)
        for i in range(0, 8):
            epd.send_data(0x00)
        if index > 0:
            for i in range(0, 21):
                epd.send_data(0xFF)
        epd.send_command(0x12) #display
