# Control the ePaper display of the DGT Centaur
#
# This method uses a thread to monitor for changes to an image
# Then any alterations to the image will show on the epaper
# You can either use the image functions in this file or modify epaper.epaperbuffer directly.
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

def saveImage():
    filename = str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg"
    epaperbuffer.save(filename)

def epaperUpdate():
    # This is used as a thread to update the e-paper if the image has changed
    global epaperbuffer
    global lastepaperhash
    global epaperprocesschange
    global kill
    print("started epaper update thread")
    epd.display(epd.getbuffer(epaperbuffer))
    time.sleep(4)
    print("epaper init image sent")
    while True and kill == 0:
        thishash = hashlib.md5(epaperbuffer.tobytes()).hexdigest()
        if thishash != lastepaperhash and epaperprocesschange == 1:
            starttime = time.time()
            im = epaperbuffer.copy()
            saveScreenToImage = threading.Thread(target=saveImage, args=())
            saveScreenToImage.daemon = True
            saveScreenToImage.start()
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            epd.DisplayPartial(epd.getbuffer(im))
            lastepaperhash = thishash
        time.sleep(0.2)

def initEpaper():
    # Set the screen to a known start state and start the epaperUpdate thread
    global epaperbuffer
    global epaperUpd
    epaperbuffer = Image.new('1', (128, 296), 255)
    print("init epaper")
    epd.init()
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
    #epaperbuffer = Image.new('1', (128, 296), 255)
    epaperbuffer = Image.open(filename)
    time.sleep(3)
    kill = 1
    time.sleep(0.5)
    epd.sleep()

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
    epaperbuffer = Image.new('1', (128, 296), 255)

