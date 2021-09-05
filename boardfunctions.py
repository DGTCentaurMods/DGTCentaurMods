# DGT Centaur board control functions
#
# I am not really a python programmer, but the language choice here
# made sense!
#
# Ed Nekebno

import serial
import sys
import os
import epd2in9d
import time
from PIL import Image, ImageDraw, ImageFont

# Open the serial port, baudrate is 1000000
ser = serial.Serial("/dev/ttyS0", baudrate=1000000, timeout=0.2)
font18 = ImageFont.truetype("/home/pi/centaur/py/Font.ttc", 18)
screenbuffer = Image.new('1', (128, 296), 255)
initialised = 0

epd = epd2in9d.EPD()


def initScreen():
    global screenbuffer
    global initialised
    epd.init()
    time.sleep(0.5)
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

def clearSerial():
    ser.read(1000000)
    tosend = bytearray(b'\x83\x06\x50\x59')
    ser.write(tosend)
    expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
    resp = ser.read(10000)
    resp = bytearray(resp)
    tosend = bytearray(b'\x94\x06\x50\x6a')
    ser.write(tosend)
    expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
    resp = ser.read(10000)

def drawBoard(pieces):
    global screenbuffer
    chessfont = Image.open("/home/pi/centaur/fonts/ChessFontSmall.bmp")
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
    time.sleep(0.1)


def doMenu(items):
    # Draw a menu, let the user navigate and return the value
    # or "BACK" if the user backed out
    # pass a menu like: menu = {'Lichess': 'Lichess', 'Centaur': 'DGT
    # Centaur', 'Shutdown': 'Shutdown', 'Reboot': 'Reboot'}
    selected = 1
    buttonPress = 0
    first = 1
    global initialised
    if initialised == 0:
        epd.Clear(0xff)
    while (buttonPress != 2):
        image = Image.new('1', (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)
        rpos = 20
        for k, v in items.items():
            draw.text((20, rpos), str(v), font=font18, fill=0)
            rpos = rpos + 20
        draw.polygon([(2, (selected * 20)), (2, (selected * 20) + 20),
                     (18, (selected * 20) + 10)], fill=0)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image = image.transpose(Image.FLIP_LEFT_RIGHT)
        if first == 1 and initialised == 0:
            epd.display(epd.getbuffer(image))
            time.sleep(3)
            first = 0
            epd.DisplayPartial(epd.getbuffer(image))
            initialised = 1
        else:
            epd.DisplayPartial(epd.getbuffer(image))
            time.sleep(0.2)
        # Next we wait for either the up/down/back or tick buttons to get
        # pressed
        timeout = time.time() + 60 * 15
        while buttonPress == 0:
            ser.read(1000000)
            tosend = bytearray(b'\x83\x06\x50\x59')
            ser.write(tosend)
            expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
            resp = ser.read(10000)
            resp = bytearray(resp)
            tosend = bytearray(b'\x94\x06\x50\x6a')
            ser.write(tosend)
            expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
            resp = ser.read(10000)
            resp = bytearray(resp)
            if (resp.hex() == "b10011065000140a0501000000007d4700"):
                buttonPress = 1
            if (resp.hex() == "b10011065000140a0510000000007d175f"):
                buttonPress = 2
            if (resp.hex() == "b10011065000140a0508000000007d3c7c"):
                buttonPress = 3
            if (resp.hex() == "b10010065000140a050200000000611d"):
                buttonPress = 4
        ser.write(bytearray(b'\xb1\x00\x08\x06\x50\x4c\x08\x63'))
        if (buttonPress == 2):
            # Tick, so return the key for this menu item
            c = 1
            r = ""
            for k, v in items.items():
                if (c == selected):
                    #epd.unsetRegion()
                    #epd.Clear(0xff)
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


def clearBoardData():
    ser.read(100000)
    tosend = bytearray(b'\x83\x06\x50\x59')
    ser.write(tosend)
    expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
    ser.read(1000000)


def waitMove():
    # Wait for a player to lift a piece and set it down somewhere different
    lifted = -1
    placed = -1
    moves = []
    while placed == -1:
        ser.read(100000)
        tosend = bytearray(b'\x83\x06\x50\x59')
        ser.write(tosend)
        expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
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
                        print(lifted)
                        moves.append(newsquare * -1)
                    if (resp[x] == 65):
                        # Calculate the square to 0(a1)-63(h8) so that
                        # all functions match
                        fieldHex = resp[x + 1]
                        newsquare = rotateFieldHex(fieldHex)
                        placed = newsquare
                        moves.append(newsquare)
                        print(placed)
        tosend = bytearray(b'\x94\x06\x50\x6a')
        ser.write(tosend)
        expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
        resp = ser.read(10000)
        resp = bytearray(resp)
    print(moves)
    return moves


def poll():
    # We need to continue poll the board to get data from it
    # Perhaps there's a packet length in here somewhere but
    # I haven't noticed it yet, therefore we need to process
    # the data as it comes
    ser.read(100000)
    tosend = bytearray(b'\x83\x06\x50\x59')
    ser.write(tosend)
    expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
    resp = ser.read(10000)
    resp = bytearray(resp)
    if (bytearray(resp) != expect):
        if (resp[0] == 133 and resp[1] == 0):
            for x in range(0, len(resp) - 1):
                if (resp[x] == 64):
                    print("PIECE LIFTED")
                    # Calculate the square to 0(a1)-63(h8) so that
                    # all functions match
                    fieldHex = resp[x + 1]
                    newsquare = rotateFieldHex(fieldHex)
                    print(newsquare)
                if (resp[x] == 65):
                    print("PIECE PLACED")
                    # Calculate the square to 0(a1)-63(h8) so that
                    # all functions match
                    fieldHex = resp[x + 1]
                    newsquare = rotateFieldHex(fieldHex)
                    print(newsquare)
    tosend = bytearray(b'\x94\x06\x50\x6a')
    ser.write(tosend)
    expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
    resp = ser.read(10000)
    resp = bytearray(resp)
    if (resp != expect):
        if (resp.hex() == "b10011065000140a0501000000007d4700"):
            print("BACK BUTTON")
        if (resp.hex() == "b10011065000140a0510000000007d175f"):
            print("TICK BUTTON")
        if (resp.hex() == "b10011065000140a0508000000007d3c7c"):
            print("UP BUTTON")
        if (resp.hex() == "b10010065000140a050200000000611d"):
            print("DOWN BUTTON")
        if (resp.hex() == "b10010065000140a0540000000006d67"):
            print("HELP BUTTON")
        if (resp.hex() == "b10010065000140a0504000000002a68"):
            print("PLAY BUTTON")


SOUND_GENERAL = 1
SOUND_FACTORY = 2
SOUND_POWER_OFF = 3
SOUND_POWER_ON = 4
SOUND_WRONG = 5
SOUND_WRONG_MOVE = 6


def beep(beeptype):
    # Ask the centaur to make a beep sound
    if (beeptype == SOUND_GENERAL):
        ser.write(bytearray(b'\xb1\x00\x08\x06\x50\x4c\x08\x63'))
    if (beeptype == SOUND_FACTORY):
        ser.write(bytearray(b'\xb1\x00\x08\x06\x50\x4c\x40\x1b'))
    if (beeptype == SOUND_POWER_OFF):
        ser.write(bytearray(b'\xb1\x00\x0a\x06\x50\x4c\x08\x48\x08\x35'))
    if (beeptype == SOUND_POWER_ON):
        ser.write(bytearray(b'\xb1\x00\x0a\x06\x50\x48\x08\x4c\x08\x35'))
    if (beeptype == SOUND_WRONG):
        ser.write(bytearray(b'\xb1\x00\x0a\x06\x50\x4e\x0c\x48\x10\x43'))
    if (beeptype == SOUND_WRONG_MOVE):
        ser.write(bytearray(b'\xb1\x00\x08\x06\x50\x48\x08\x5f'))


def ledsOff():
    # Switch the LEDs off on the centaur
    ser.write(bytearray(b'\xb0\x00\x07\x06\x50\x00\x0d'))


def ledFromTo(lfrom, lto):
    # Light up a from and to LED for move indication
    # Note the call to this function is 0 for a1 and runs to 63 for h8
    # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
    tosend = bytearray(b'\xb0\x00\x0c\x06\x50\x05\x03\x00\x05\x3d\x31\x0d')
    # Recalculate lfrom to the different indexing system
    tosend[9] = rotateField(lfrom)
    # Same for lto
    tosend[10] = rotateField(lto)
    # Wipe checksum byte and append the new checksum.
    tosend.pop()
    tosend.append(checksum(tosend))
    ser.write(tosend)
    # Read off any data
    ser.read(100000)

def led(num):
    # Flashes a specific led
    # Note the call to this function is 0 for a1 and runs to 63 for h8
    # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
    tosend = bytearray(b'\xb0\x00\x0b\x06\x50\x05\x0a\x01\x01\x3d\x5f')
    # Recalculate num to the different indexing system
    # Last bit is the checksum
    tosend[9] = rotateField(num)
    # Wipe checksum byte and append the new checksum.
    tosend.pop()
    tosend.append(checksum(tosend))
    ser.write(tosend)
    # Read off any data
    ser.read(100000)

def ledFlash():
    # Flashes the last led lit by led(num) above
    tosend = bytearray(b'\xb0\x00\x0a\x06\x50\x05\x0a\x00\x01\x20')
    ser.write(tosend)
    ser.read(100000)

def checksum(barr):
    csum = 0
    for c in bytes(barr):
        csum += c
    barr_csum = (csum % 128)
    return barr_csum

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

def shutdown():
    """
    Initiate shutdown sequence.
    """
    initScreen()
    clearScreenBuffer()
    sleepScreen()
    tosend = bytearray(b'\xb2\x00\x07\x06\x50\x0a\x19')
    ser.write(tosend)



# poll()
# beep(SOUND_GENERAL)
# ledsOff()
# ledFromTo(0,63)
# while True:
#	poll()
# sys.exit()
