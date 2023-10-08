# DGT Centaur board control functions
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

import serial
import sys
import os
from DGTCentaurMods.display import epd2in9d, epaper
from DGTCentaurMods.display.ui_components import AssetManager
from DGTCentaurMods.board.settings import Settings
from DGTCentaurMods.board import centaur
import time
from PIL import Image, ImageDraw, ImageFont
import pathlib
import socket
import queue
import logging

try:
    logging.basicConfig(level=logging.DEBUG, filename="/home/pi/debug.log",filemode="w")
except:
    logging.basicConfig(level=logging.DEBUG)

#
# Useful constants
#
SOUND_GENERAL = 1
SOUND_FACTORY = 2
SOUND_POWER_OFF = 3
SOUND_POWER_ON = 4
SOUND_WRONG = 5
SOUND_WRONG_MOVE = 6
BTNBACK = 1
BTNTICK = 2
BTNUP = 3
BTNDOWN = 4
BTNHELP = 5
BTNPLAY = 6
BTNLONGPLAY = 7

# Get the config
dev = Settings.read('system', 'developer', 'False')

# Various setup
if dev == "True":
    logging.debug("Developer mode is: ",dev)
    # Enable virtual serial port
    # TODO: setup as a service
    os.system("socat -d -d pty,raw,echo=0 pty,raw,echo=0 &")
    time.sleep(10)
    # Then redirect
    ser = serial.Serial("/dev/pts/2", baudrate=1000000, timeout=0.2)
else:
    try:
        ser = serial.Serial("/dev/serial0", baudrate=1000000, timeout=0.2) 
        ser.isOpen()
    except:
        ser.close()
        ser.open()

font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
time.sleep(2)


# Battery related
chargerconnected = 0
batterylevel = -1
batterylastchecked = 0

# But the address might not be that :( Here we send an initial 0x4d to ask the board to provide its address
logging.debug("Detecting board adress")
try:
    ser.read(1000)
except:
    ser.read(1000)
tosend = bytearray(b'\x4d')
ser.write(tosend)
try:
    ser.read(1000)
except:
    ser.read(1000)
logging.debug('Sent payload 1')
tosend = bytearray(b'\x4e')
ser.write(tosend)
try:
    ser.read(1000)
except:
    ser.read(1000)
logging.debug('Sent payload 2')
logging.debug('Serial is open. Waiting for response.')
resp = ""
# This is the most common address of the board
addr1 = 00
addr2 = 00
timeout = time.time() + 60
while len(resp) < 4 and time.time() < timeout:
    if dev == "True":
        break
    tosend = bytearray(b'\x87\x00\x00\x07')
    ser.write(tosend)
    try:
        resp = ser.read(1000)
    except:
        resp = ser.read(1000)
    if len(resp) > 3:
        addr1 = resp[3]
        addr2 = resp[4]
        logging.debug("Discovered new address:" + hex(addr1) + hex(addr2))
        break
else:
    logging.debug('FATAL: No response from serial')
    sys.exit(1)

def checksum(barr):
    csum = 0
    for c in bytes(barr):
        csum += c
    barr_csum = (csum % 128)
    return barr_csum

def buildPacket(command, data):
    # pass command and data as bytes
    tosend = bytearray(command + addr1.to_bytes(1,byteorder='big') + addr2.to_bytes(1,byteorder='big') + data)
    tosend.append(checksum(tosend))
    return tosend

def sendPacket(command, data):
    # pass command and data as bytes
    tosend = buildPacket(command, data)
    ser.write(tosend)


def clearSerial():
    logging.debug('Checking and clear the serial line.')
    resp1 = ""
    resp2 = ""
    while dev == "False" and True:
        sendPacket(b'\x83', b'')
        expect1 = buildPacket(b'\x85\x00\x06', b'')
        try:
            resp1 = ser.read(256)
        except:
            pass
        sendPacket(b'\x94', b'')
        expect2 = buildPacket(b'\xb1\x00\x06', b'')
        try:
            resp2 = ser.read(256)
        except:
            pass
        #If board is idle, return True
        if expect1 == resp1 and expect2 == resp2:
            logging.debug('Board is idle. Serial is clear.')
            return True
        else:
            logging.debug('  Attempting to clear serial')

# Screen functions - deprecated, use epaper.py if possible
#

screenbuffer = Image.new('1', (128, 296), 255)
initialised = 0
epd = epd2in9d.EPD()

def initScreen():
    global screenbuffer
    global initialised
    epd.init()
    epd.Clear(0xff)
    screenbuffer = Image.new('1', (128, 296), 255)
    initialised = 0
    time.sleep(4)

def clearScreen():
    epd.Clear(0xff)

def clearScreenBuffer():
    global screenbuffer
    screenbuffer = Image.new('1', (128, 296), 255)

def sleepScreen():
    epd.sleep()

def drawBoard(pieces):
    global screenbuffer
    chessfont = Image.open(AssetManager.get_resource_path("chesssprites.bmp"))
    image = screenbuffer.copy()
    for x in range(0,64):
        pos = (x - 63) * -1
        row = 50 + (16 * (pos // 8))
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
        image.paste(piece,(col, row))
    screenbuffer = image.copy()
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    epd.DisplayPartial(epd.getbuffer(image))
    time.sleep(0.1)

def writeText(row, txt):
    # Writes some text on the screen at the given row
    rpos = row * 20
    global screenbuffer
    image = screenbuffer.copy()
    draw = ImageDraw.Draw(image)
    draw.rectangle([(0,rpos),(128,rpos+20)],fill=255)
    draw.text((0, rpos), txt, font=font18, fill=0)
    screenbuffer = image.copy()
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    epd.DisplayPartial(epd.getbuffer(image))
    time.sleep(0.5)

def writeTextToBuffer(row, txt):
    # Writes some text on the screen at the given row
    # Writes only to the screen buffer. Script can later call displayScreenBufferPartial to show it
    global screenbuffer
    nimage = screenbuffer.copy()
    image = Image.new('1', (128, 20), 255)
    draw = ImageDraw.Draw(image)
    draw.text((0,0), txt, font=font18, fill=0)
    nimage.paste(image, (0, (row * 20)))
    screenbuffer = nimage.copy()

def promotionOptionsToBuffer(row):
    # Draws the promotion options to the screen buffer
    global screenbuffer
    nimage = screenbuffer.copy()
    image = Image.new('1', (128, 20), 255)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), "    Q    R    N    B", font=font18, fill=0)
    draw.polygon([(2, 18), (18, 18), (10, 3)], fill=0)
    draw.polygon([(35, 3), (51, 3), (43, 18)], fill=0)
    o = 66
    draw.line((0+o,16,16+o,16), fill=0, width=5)
    draw.line((14+o,16,14+o,5), fill=0, width=5)
    draw.line((16+o,6,4+o,6), fill=0, width=5)
    draw.polygon([(8+o, 2), (8+o, 10), (0+o, 6)], fill=0)
    o = 97
    draw.line((6+o,16,16+o,4), fill=0, width=5)
    draw.line((2+o,10, 8+o,16), fill=0, width=5)
    nimage.paste(image, (0, (row * 20)))
    screenbuffer = nimage.copy()

def displayScreenBufferPartial():
    global screenbuffer
    image = screenbuffer.copy()
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    epd.DisplayPartial(epd.getbuffer(image))
    time.sleep(0.1)

def doMenu(items, fast = 0):
    # Draw a menu, let the user navigate and return the value
    # or "BACK" if the user backed out
    # pass a menu like: menu = {'Lichess': 'Lichess', 'Centaur': 'DGT
    # Centaur', 'Shutdown': 'Shutdown', 'Reboot': 'Reboot'}
    selected = 1
    buttonPress = 0
    first = 1
    global initialised
    #if initialised == 0 and fast == 0:
    #    epd.Clear(0xff)
    connected = 0
    if fast == 0:
        connected = checkInternetSocket()
    quickselect = 0
    quickselectpossible = -1
    res = getBoardState()
    if res[32] == 0 and res[33] == 0 and res[34] == 0 and res[35] == 0 and res[36]==0 and res[37] == 0 and res[38] == 0 and res[39] == 0:
        # If the 4th rank is empty then enable quick select mode. Then we can choose a menu option by placing and releasing a piece
        quickselect = 1
    image = Image.new('1', (epd.width, epd.height), 255)
    while (buttonPress != 2):
        time.sleep(0.05)
        draw = ImageDraw.Draw(image)
        if first == 1:
            rpos = 20
            draw.rectangle([(0,0),(127,295)], fill=255, outline=255)
            for k, v in items.items():
                draw.text((20, rpos), str(v), font=font18, fill=0)
                rpos = rpos + 20
            draw.rectangle([(-1, 0), (17, 294)], fill=255, outline=0)
            draw.polygon([(2, (selected * 20) + 2), (2, (selected * 20) + 18),
                          (18, (selected * 20) + 10)], fill=0)
            # Draw an image representing internet connectivity
            wifion = Image.open(AssetManager.get_resource_path("wifiontiny.bmp"))
            wifioff = Image.open(AssetManager.get_resource_path("wifiofftiny.bmp"))
            if connected == True:
                wifidispicon = wifion.resize((20,16))
                image.paste(wifidispicon, (105, 5))
            else:
                wifidispicon = wifioff.resize((20, 16))
                image.paste(wifidispicon, (105, 5))
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        draw.rectangle([(110,0),(128,294)],fill=255,outline=0)
        draw.polygon([(128 - 2, 276 - (selected * 20) + 2), (128 - 2, 276 - (selected * 20) + 18),
                      (128 - 18, 276 - (selected * 20) + 10)], fill=0)

        if first == 1 and initialised == 0:
            if fast == 0:
                epd.init()
                epd.display(epd.getbuffer(image))
            first = 0
            epd.DisplayRegion(0,295,epd.getbuffer(image))
            time.sleep(2)
            initialised = 1
        else:
            if first == 1 and initialised == 1:
                first = 0
                epd.DisplayRegion(0, 295, epd.getbuffer(image))
                time.sleep(2)
            else:
                sl = 295 - (selected * 20) - 40
                epd.DisplayRegion(sl,sl + 60,epd.getbuffer(image.crop((0,sl,127,sl+60))))

        # Next we wait for either the up/down/back or tick buttons to get
        # pressed
        timeout = time.time() + 60 * 15
        while buttonPress == 0:
            ser.read(1000000)
            sendPacket(b'\x83', b'')
            expect = buildPacket(b'\x85\x00', b'')
            resp = ser.read(10000)
            resp = bytearray(resp)
            sendPacket(b'\x94', b'')
            expect = buildPacket(b'\xb1\x00', b'')
            resp = ser.read(10000)
            resp = bytearray(resp)
            if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0501000000007d47"):
                buttonPress = 1
            if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0510000000007d17"):
                buttonPress = 2
            if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0508000000007d3c"):
                buttonPress = 3
            if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a05020000000061"):
                buttonPress = 4
            # check for quickselect
            if quickselect == 1 and quickselectpossible < 1:
                res = getBoardState()
                if res[32] > 0:
                    quickselectpossible = 1
                if res[33] > 0:
                    quickselectpossible = 2
                if res[34] > 0:
                    quickselectpossible = 3
                if res[35] > 0:
                    quickselectpossible = 4
                if res[36] > 0:
                    quickselectpossible = 5
                if res[37] > 0:
                    quickselectpossible = 6
                if res[38] > 0:
                    quickselectpossible = 7
                if res[39] > 0:
                    quickselectpossible = 8
                if quickselectpossible > 0:
                    beep(SOUND_GENERAL)
            if quickselect == 1 and quickselectpossible > 0:
                res = getBoardState()
                if res[32] == 0 and res[33] == 0 and res[34] == 0 and res[35] == 0 and res[36] == 0 and res[37] == 0 and res[38] == 0 and res[39] == 0:
                    # Quickselect possible has been chosen
                    c = 1
                    r = ""
                    for k, v in items.items():
                        if (c == quickselectpossible):
                            # epd.unsetRegion()
                            # epd.Clear(0xff)
                            selected = 99999
                            return k
                        c = c + 1

        sendPacket(b'\xb1\x00\x08', b'\x4c\x08')
        if (buttonPress == 2):
            # Tick, so return the key for this menu item
            c = 1
            r = ""
            for k, v in items.items():
                if (c == selected):
                    selected = 99999
                    return k
                c = c + 1
        if (buttonPress == 4 and selected < len(items)):
            selected = selected + 1
        if (buttonPress == 3 and selected > 1):
            selected = selected - 1
        if (buttonPress == 1):
            epd.Clear(0xff)
            return "BACK"
        if time.time() > timeout:
            epd.Clear(0xff)
            return "BACK"
        buttonPress = 0

#
# Board control - functions related to making the board do something
#

def clearBoardData():
    ser.read(100000)
    sendPacket(b'\x83', b'')
    expect = buildPacket(b'\x85\x00\x06', b'')
    ser.read(1000000)

def beep(beeptype):
    # Ask the centaur to make a beep sound
    if centaur.get_sound() == "off":
        return
    if (beeptype == SOUND_GENERAL):
        sendPacket(b'\xb1\x00\x08',b'\x4c\x08')
    if (beeptype == SOUND_FACTORY):
        sendPacket(b'\xb1\x00\x08', b'\x4c\x40')
    if (beeptype == SOUND_POWER_OFF):
        sendPacket(b'\xb1\x00\x0a', b'\x4c\x08\x48\x08')
    if (beeptype == SOUND_POWER_ON):
        sendPacket(b'\xb1\x00\x0a', b'\x48\x08\x4c\x08')
    if (beeptype == SOUND_WRONG):
        sendPacket(b'\xb1\x00\x0a', b'\x4e\x0c\x48\x10')
    if (beeptype == SOUND_WRONG_MOVE):
        sendPacket(b'\xb1\x00\x08', b'\x48\x08')

def ledsOff():
    # Switch the LEDs off on the centaur
    sendPacket(b'\xb0\x00\x07', b'\x00')

def ledArray(inarray, speed = 3, intensity=5):
    # Lights all the leds in the given inarray with the given speed and intensity
    tosend = bytearray(b'\xb0\x00\x0c' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big') + b'\x05')
    tosend.append(speed)
    tosend.append(0)
    tosend.append(intensity)
    for i in range(0, len(inarray)):
        tosend.append(rotateField(inarray[i]))
    tosend[2] = len(tosend) + 1
    tosend.append(checksum(tosend))
    ser.write(tosend)

def ledFromTo(lfrom, lto, intensity=5):
    # Light up a from and to LED for move indication
    # Note the call to this function is 0 for a1 and runs to 63 for h8
    # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
    tosend = bytearray(b'\xb0\x00\x0c' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big') + b'\x05\x03\x00\x05\x3d\x31\x0d')
    # Recalculate lfrom to the different indexing system
    tosend[8] = intensity
    tosend[9] = rotateField(lfrom)
    # Same for lto
    tosend[10] = rotateField(lto)
    # Wipe checksum byte and append the new checksum.
    tosend.pop()
    tosend.append(checksum(tosend))
    ser.write(tosend)
    # Read off any data
    #ser.read(100000)

def led(num, intensity=5):
    # Flashes a specific led
    # Note the call to this function is 0 for a1 and runs to 63 for h8
    # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
    tcount = 0
    success = 0
    while tcount < 5 and success == 0:
        try:
            tosend = bytearray(b'\xb0\x00\x0b' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big') + b'\x05\x0a\x01\x01\x3d\x5f')
            # Recalculate num to the different indexing system
            # Last bit is the checksum
            tosend[8] = intensity
            tosend[9] = rotateField(num)
            # Wipe checksum byte and append the new checksum.
            tosend.pop()
            tosend.append(checksum(tosend))
            ser.write(tosend)
            success = 1
            # Read off any data
            #ser.read(100000)
        except:
            time.sleep(0.1)
            tcount = tcount + 1

def ledFlash():
    # Flashes the last led lit by led(num) above
    sendPacket(b'\xb0\x00\x0a', b'\x05\x0a\x00\x01')
    #ser.read(100000)


def shutdown():
    update = centaur.UpdateSystem()
    beep(SOUND_POWER_OFF)
    package = '/tmp/dgtcentaurmods_armhf.deb'
    if os.path.exists(package):
        ledArray([0,1,2,3,4,5,6,7],6)
        epaper.clearScreen()
        update.updateInstall()
        return
    logging.debug('Normal shutdown')
    epaper.clearScreen()
    time.sleep(1)
    ledFromTo(7,7)
    epaper.writeText(3, "     Shutting")
    epaper.writeText(4, "       down")
    time.sleep(3)
    epaper.stopEpaper()
    os.system("sudo poweroff")


def sleep():
    """
    Sleep the controller.
    """
    sendPacket(b'\xb2\x00\x07', b'\x0a')


#
# Board response - functions related to get something from the board
#

def waitMove():
    # Wait for a player to lift a piece and set it down somewhere different
    lifted = -1
    placed = -1
    moves = []
    while placed == -1:
        ser.read(100000)
        sendPacket(b'\x83', b'')
        expect = buildPacket(b'\x85\x00\x06', b'')
        resp = ser.read(10000)
        resp = bytearray(resp)
        if (bytearray(resp) != expect):
            if (resp[0] == 133 and resp[1] == 0):
                for x in range(0, len(resp) - 1):
                    if (resp[x] == 64):
                        # Calculate the square to 0(a1)-63(h8) so that
                        # all functions match
                        fieldHex = resp[x + 1]
                        newsquare = rotateFieldHex(fieldHex)
                        lifted = newsquare
                        moves.append((newsquare+1) * -1)
                    if (resp[x] == 65):
                        # Calculate the square to 0(a1)-63(h8) so that
                        # all functions match
                        fieldHex = resp[x + 1]
                        newsquare = rotateFieldHex(fieldHex)
                        placed = newsquare
                        moves.append(newsquare + 1)
        sendPacket(b'\x94', b'')
        expect = buildPacket(b'\xb1\x00\x06', b'')
        resp = ser.read(10000)
        resp = bytearray(resp)
    return moves

def poll():
    # We need to continue poll the board to get data from it
    # Perhaps there's a packet length in here somewhere but
    # I haven't noticed it yet, therefore we need to process
    # the data as it comes
    ser.read(100000)
    sendPacket(b'\x83', b'')
    expect = buildPacket(b'\x85\x00\x06', b'')
    resp = ser.read(10000)
    resp = bytearray(resp)
    if (bytearray(resp) != expect):
        if (resp[0] == 133 and resp[1] == 0):
            for x in range(0, len(resp) - 1):
                if (resp[x] == 64):
                    # Calculate the square to 0(a1)-63(h8) so that
                    # all functions match
                    fieldHex = resp[x + 1]
                    newsquare = rotateFieldHex(fieldHex)
                if (resp[x] == 65):
                    # Calculate the square to 0(a1)-63(h8) so that
                    # all functions match
                    fieldHex = resp[x + 1]
                    newsquare = rotateFieldHex(fieldHex)
    sendPacket(b'\x94', b'')
    expect = buildPacket(b'\xb1\x00\x06', b'')
    resp = ser.read(10000)
    resp = bytearray(resp)
    if (resp != expect):
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0501000000007d47"):
            logging.debug("BACK BUTTON")
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0510000000007d17"):
            logging.debug("TICK BUTTON")
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0508000000007d3c"):
            logging.debug("UP BUTTON")
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a05020000000061"):
            logging.debug("DOWN BUTTON")
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0540000000006d"):
            logging.debug("HELP BUTTON")
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0504000000002a"):
            logging.debug("PLAY BUTTON")

def getText(title):
    # Allows text to be entered using a virtual keyboard where a chess piece
    # is placed on the board in the correct position
    global screenbuffer
    clearstate = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    printableascii = " !\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~                                                                "
    charpage = 1
    typed = ""
    # First we need a clear board
    res = getBoardState()
    if bytearray(res) != clearstate:
        writeTextToBuffer(0,'Remove board')
        writeText(1,'pieces')
        time.sleep(10)
        while bytearray(res) != clearstate:
            time.sleep(0.5)
            res = getBoardState()
    changed = 1
    clearBoardData()
    while True:
        if changed == 1:
            # print our title and our box that the answer will go in
            image = screenbuffer.copy()
            draw = ImageDraw.Draw(image)
            draw.rectangle([(0, 0), (128, 250)], fill=255)
            draw.text((0,20),title, font=font18, fill=0)
            draw.rectangle([(0,39),(128,61)],fill=255,outline=0)
            tt = typed
            if len(tt) > 10:
                tt = tt[-11:]
            draw.text((0,40),tt, font=font18, fill=0)
            # Using the current charpage display the symbols that a square would represent
            pos = (charpage -1) * 64
            lchars = []
            for i in range(pos,pos+64):
                lchars.append(printableascii[i])
            pos = 0
            for i in range(0,len(lchars),8):
                tsts = ""
                for q in range(0,8):
                    tsts = tsts + lchars[i + q]
                    draw.text(((q*16),(pos*20)+80),lchars[i + q], font=font18, fill=0)
                pos = pos + 1
            screenbuffer = image.copy()
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            epd.DisplayPartial(epd.getbuffer(image))
            time.sleep(0.1)
            changed = 0
        buttonPress = 0
        ser.read(1000000)
        sendPacket(b'\x83', b'')
        expect = buildPacket(b'\x85\x00\x06', b'')
        resp = ser.read(10000)
        resp = bytearray(resp)
        # If a piece is placed it will type a character!
        if (bytearray(resp) != expect):
            if (resp[0] == 133 and resp[1] == 0):
                for x in range(0, len(resp) - 1):
                    if resp[x] == 65:
                        # Calculate the square to 0(a1)-63(h8) so that
                        # all functions match
                        fieldHex = resp[x + 1]
                        typed = typed + lchars[fieldHex]
                        beep(SOUND_GENERAL)
                        changed = 1
        sendPacket(b'\x94', b'')
        expect = buildPacket(b'\xb1\x00\x06', b'')
        resp = ser.read(10000)
        resp = bytearray(resp)
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0501000000007d47"):
            buttonPress = 1 # BACK
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0510000000007d17"):
            buttonPress = 2 # TICK
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0508000000007d3c"):
            buttonPress = 3 # UP
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a05020000000061"):
            buttonPress = 4 # DOWN
        if buttonPress == 1 and len(typed) > 0:
            typed = typed[:-1]
            beep(SOUND_GENERAL)
            changed = 1
        if buttonPress == 2:
            beep(SOUND_GENERAL)
            clearScreen()
            time.sleep(1)
            return typed
        if buttonPress == 3:
            beep(SOUND_GENERAL)
            charpage = 1
            changed = 1
        if buttonPress == 4:
            beep(SOUND_GENERAL)
            charpage = 2
            changed = 1
        time.sleep(0.2)

def getBoardState(field=None):
    # Query the board and return a representation of it
    # Consider this function experimental
    # lowerlimit/upperlimit may need adjusting
    # Get the board data
    resp = []
    while (len(resp) < 64):
        sendPacket(b'\xf0\x00\x07', b'\x7f')
        resp = ser.read(10000)
        if (len(resp) < 64):
            time.sleep(0.5)
    resp = resp = resp[6:(64 * 2) + 6]
    boarddata = [None] * 64
    for x in range(0, 127, 2):
        tval = (resp[x] * 256) + resp[x+1]
        boarddata[(int)(x/2)] = tval
    # Any square lower than 400 is empty
    # Any square higher than upper limit is also empty
    upperlimit = 32000
    lowerlimit = 300
    for x in range(0,64):
        if ((boarddata[x] < lowerlimit) or (boarddata[x] > upperlimit)):
            boarddata[x] = 0
        else:
            boarddata[x] = 1
    if field:
        return boarddata[field]
    return boarddata

def printBoardState():
    # Helper to display board state
    state = getBoardState()
    for x in range(0,64,8):
        print("+---+---+---+---+---+---+---+---+")
        for y in range(0,8):
            print("| " + str(state[x+y]) + " ", end='')
        print("|\r")
    print("+---+---+---+---+---+---+---+---+")

def getChargingState():
    # Returns if the board is plugged into the charger or not
    # 0 = not plugged in, 1 = plugged in, -1 = error in checking
    resp = ""
    timeout = time.time() + 5
    while len(resp) < 7 and time.time() < timeout:
        # Sending the board a packet starting with 152 gives battery info
        sendPacket(bytearray([152]), b'')
        try:
            resp = ser.read(1000)
        except:
            pass
        if len(resp) < 7:
            pass
        else:  
            if resp[0] == 181:
                vall = (resp[5] >> 5) & 7
                if vall == 1:
                    return 1
                else:
                    return 0
    return - 1

def getBatteryLevel():
    # Returns a number 0 - 20 representing battery level of the board
    # 20 is fully charged. The board dies somewhere around a low of 1
    resp = ""
    timeout = time.time() + 5
    while len(resp) < 7 and time.time() < timeout:
        # Sending the board a packet starting with 152 gives battery info
        sendPacket(bytearray([152]), b'')
        try:
            resp = ser.read(1000)
        except:
            pass
    if len(resp) < 7:
        return -1
    else:        
        if resp[0] == 181:
            vall = resp[5] & 31
            return vall
    

#
# Miscellaneous functions - do they belong in this file?
#

def checkInternetSocket(host="8.8.8.8", port=53, timeout=1):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        logging.debug(ex)
        return False

#
# Helper functions - used by other functions or useful in manipulating board data
#

def rotateField(field):
    lrow = (field // 8)
    lcol = (field % 8)
    newField = (7 - lrow) * 8 + lcol
    return newField

def rotateFieldHex(fieldHex):
    squarerow = (fieldHex // 8)
    squarecol = (fieldHex % 8)
    field = (7 - squarerow) * 8 + squarecol
    return field

def convertField(field):
    square = chr((ord('a') + (field % 8))) + chr(ord('1') + (field // 8))
    return square


# This section is the start of a new way of working with the board functions where those functions are
# the board returning some kind of data
import threading
eventsthreadpointer = ""
eventsrunning = 1

def temp():
    '''
    Get CPU temperature
    '''
    temp = os.popen("vcgencmd measure_temp | cut -d'=' -f2").read().strip()
    return temp

def eventsThread(keycallback, fieldcallback, tout):
    # This monitors the board for events
    # keypresses and pieces lifted/placed down
    global eventsrunning
    global standby
    global batterylevel
    global batterylastchecked
    global chargerconnected
    standby = False
    hold_timeout = False
    events_paused = False
    to = time.time() + tout
    logging.debug('Timeout at ' + str(tout) + ' seconds')
    while time.time() < to:
        loopstart = time.time()
        if eventsrunning == 1:
            # Hold and restart timeout on charger attached
            if chargerconnected == 1:
                to = time.time() + 100000
                hold_timeout = True
            if chargerconnected == 0 and hold_timeout:
                to = time.time() + tout
                hold_timeout = False

            # Reset timeout on unPauseEvents
            if events_paused:
                to = time.time() + tout
                events_paused = False

            buttonPress = 0
            if not standby:
                #Hold fields activity on standby
                if fieldcallback != None:
                    try:
                        sendPacket(b'\x83', b'')
                        expect = bytearray(b'\x85\x00\x06' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big'))
                        expect.append(checksum(expect))
                        resp = ser.read(10000)
                        resp = bytearray(resp)
                        if (bytearray(resp) != expect):
                            if (resp[0] == 133 and resp[1] == 0):
                                for x in range(0, len(resp) - 1):
                                    if (resp[x] == 64):
                                        # Calculate the square to 0(a1)-63(h8) so that
                                        # all functions match
                                        fieldHex = resp[x + 1]
                                        newsquare = rotateFieldHex(fieldHex)
                                        fieldcallback(newsquare + 1)
                                        to = time.time() + tout
                                    if (resp[x] == 65):
                                        #print("PIECE PLACED")
                                        # Calculate the square to 0(a1)-63(h8) so that
                                        # all functions match
                                        fieldHex = resp[x + 1]
                                        newsquare = rotateFieldHex(fieldHex)
                                        fieldcallback((newsquare + 1) * -1)
                                        to = time.time() + tout
                    except:
                        pass
           
            try:
                sendPacket(b'\x94', b'')
                expect = bytearray(b'\xb1\x00\x06' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big'))
                expect.append(checksum(expect))
                resp = ser.read(10000)
                resp = bytearray(resp)
                if not standby:
                    #Disable these buttons on standby
                    if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0501000000007d47"):
                        to = time.time() + tout
                        buttonPress = BTNBACK  # BACK
                    if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0510000000007d17"):
                        to = time.time() + tout
                        buttonPress = BTNTICK  # TICK
                    if (resp.hex()[:-2] == "b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0508000000007d3c"):
                        to = time.time() + tout
                        buttonPress = BTNUP  # UP
                    if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a05020000000061"):
                        to = time.time() + tout
                        buttonPress = BTNDOWN  # DOWN
                    if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0540000000006d"):
                        to = time.time() + tout
                        buttonPress = BTNHELP   # HELP
                if (resp.hex()[:-2] == "b10010" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0504000000002a"):
                    breaktime = time.time() + 0.5
                    beep(SOUND_GENERAL)
                    while time.time() < breaktime:
                        sendPacket(b'\x94', b'')
                        expect = bytearray(b'\xb1\x00\x06' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big'))
                        expect.append(checksum(expect))
                        resp = ser.read(1000)
                        resp = bytearray(resp)
                        if resp.hex().startswith("b10011" + "{:02x}".format(addr1) + "{:02x}".format(addr2) + "00140a0500040"):
                            logging.debug('Play btn pressed. Stanby is:',standby)
                            if standby == False:
                                logging.debug('Calling standbyScreen()')
                                epaper.standbyScreen(True)
                                standby = True
                                logging.debug('Starting shutdown countdown')
                                sd = threading.Timer(600,shutdown)
                                sd.start()
                                to = time.time() + 100000
                                break
                            else:
                                clearSerial()
                                epaper.standbyScreen(False)
                                logging.debug('Cancel shutdown')
                                sd.cancel()
                                standby = False
                                to = time.time() + tout
                                break
                            break
                    else:
                        beep(SOUND_POWER_OFF)
                        shutdown()
            except:
                pass
            try:
                # Sending 152 to the controller provides us with battery information
                # Do this every 30 seconds and fill in the globals
                if time.time() - batterylastchecked > 15:
                    # Every 5 seconds check the battery details
                    resp = ""
                    timeout = time.time() + 4
                    while len(resp) < 7 and time.time() < timeout:
                        # Sending the board a packet starting with 152 gives battery info
                        sendPacket(bytearray([152]), b'')
                        try:
                            resp = ser.read(1000)
                        except:
                            pass
                    if len(resp) < 7:
                        pass
                    else:        
                        if resp[0] == 181:                            
                            batterylastchecked = time.time()
                            batterylevel = resp[5] & 31
                            vall = (resp[5] >> 5) & 7                            
                            if vall == 1 or vall == 2:
                                chargerconnected = 1
                            else:
                                chargerconnected = 0
            except:
                pass
            time.sleep(0.05)
            if buttonPress != 0:
                to = time.time() + tout
                keycallback(buttonPress)
        else:
            # If pauseEvents() hold timeout in the thread
            to = time.time() + 100000
            events_paused = True

        if time.time() - loopstart > 30:
            to = time.time() + tout
        time.sleep(0.05)
    else:
        # Timeout reached, while loop breaks. Shutdown.
        logging.debug('Timeout. Shutting doen')
        shutdown()


def subscribeEvents(keycallback, fieldcallback, timeout=100000):
    # Called by any program wanting to subscribe to events
    # Arguments are firstly the callback function for key presses, secondly for piece lifts and places
    clearSerial()
    eventsthreadpointer = threading.Thread(target=eventsThread, args=([keycallback, fieldcallback, timeout]))
    eventsthreadpointer.daemon = True
    eventsthreadpointer.start()

def pauseEvents():
    global eventsrunning
    eventsrunning = 0
    time.sleep(0.5)

def unPauseEvents():
    global eventsrunning
    eventsrunning = 1


