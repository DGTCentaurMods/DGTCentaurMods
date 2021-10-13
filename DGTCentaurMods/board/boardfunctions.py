# DGT Centaur board control functions
#
# I am not really a python programmer, but the language choice here
# made sense!
#
# Ed Nekebno

import serial
import sys
import os
from DGTCentaurMods.display import epd2in9d
import time
from PIL import Image, ImageDraw, ImageFont
import pathlib
import socket
import queue

# Open the serial port, baudrate is 1000000
ser = serial.Serial("/dev/ttyS0", baudrate=1000000, timeout=0.2)
font18 = ImageFont.truetype(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/Font.ttc", 18)
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
        writeText(0,'Remove board')
        writeText(1,'pieces')
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
        tosend = bytearray(b'\x83\x06\x50\x59')
        ser.write(tosend)
        expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
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
        tosend = bytearray(b'\x94\x06\x50\x6a')
        ser.write(tosend)
        expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
        resp = ser.read(10000)
        resp = bytearray(resp)
        if (resp.hex() == "b10011065000140a0501000000007d4700"):
            buttonPress = 1 # BACK
        if (resp.hex() == "b10011065000140a0510000000007d175f"):
            buttonPress = 2 # TICK
        if (resp.hex() == "b10011065000140a0508000000007d3c7c"):
            buttonPress = 3 # UP
        if (resp.hex() == "b10010065000140a050200000000611d"):
            buttonPress = 4 # DOWN
        if buttonPress == 1 and len(typed) > 0:
            typed = typed[:-1]
            beep(SOUND_GENERAL)
            changed = 1
        if buttonPress == 2:
            beep(SOUND_GENERAL)
            initScreen()
            time.sleep(2)
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

def checkInternetSocket(host="8.8.8.8", port=53, timeout=1):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False

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
            wifion = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/wifiontiny.bmp")
            wifioff = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/wifiofftiny.bmp")
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
                    #epd.display(epd.getbuffer(image))
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


def ledFromTo(lfrom, lto, intensity=5):
    # Light up a from and to LED for move indication
    # Note the call to this function is 0 for a1 and runs to 63 for h8
    # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
    tosend = bytearray(b'\xb0\x00\x0c\x06\x50\x05\x03\x00\x05\x3d\x31\x0d')
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
    ser.read(100000)

def led(num, intensity=5):
    # Flashes a specific led
    # Note the call to this function is 0 for a1 and runs to 63 for h8
    # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
    tosend = bytearray(b'\xb0\x00\x0b\x06\x50\x05\x0a\x01\x01\x3d\x5f')
    # Recalculate num to the different indexing system
    # Last bit is the checksum
    tosend[8] = intensity
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

def getBoardState(field=None):
    # Query the board and return a representation of it
    # Consider this function experimental
    # lowerlimit/upperlimit may need adjusting
    # Get the board data
    tosend = bytearray(b'\xf0\x00\x07\x06\x50\x7f\x4c')
    ser.write(tosend)
    resp = ser.read(10000)
    resp = resp = resp[6:(64 * 2) + 6]
    boarddata = [None] * 64
    for x in range(0, 127, 2):
        tval = (resp[x] * 256) + resp[x+1];
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

# This section is the start of a new way of working with the board functions
import threading
eventsthreadpointer = ""
eventsrunning = 1

BTNBACK = 1
BTNTICK = 2
BTNUP = 3
BTNDOWN = 4
BTNHELP = 5
BTNPLAY = 6

def eventsThread(keycallback, fieldcallback):
    # This monitors the board for events
    # at the moment it only records keypress
    global eventsrunning
    while True:
        if eventsrunning == 1:
            buttonPress = 0
            try:
                tosend = bytearray(b'\x83\x06\x50\x59')
                ser.write(tosend)
                expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
                resp = ser.read(10000)
                resp = bytearray(resp)
                if (bytearray(resp) != expect):
                    if (resp[0] == 133 and resp[1] == 0):
                        for x in range(0, len(resp) - 1):
                            if (resp[x] == 64):
                                #print("PIECE LIFTED")
                                # Calculate the square to 0(a1)-63(h8) so that
                                # all functions match
                                fieldHex = resp[x + 1]
                                newsquare = rotateFieldHex(fieldHex)
                                fieldcallback(newsquare)
                            if (resp[x] == 65):
                                #print("PIECE PLACED")
                                # Calculate the square to 0(a1)-63(h8) so that
                                # all functions match
                                fieldHex = resp[x + 1]
                                newsquare = rotateFieldHex(fieldHex)
                                fieldcallback(newsquare * -1)
            except:
                pass
            try:
                tosend = bytearray(b'\x94\x06\x50\x6a')
                ser.write(tosend)
                expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
                resp = ser.read(10000)
                resp = bytearray(resp)
                if (resp.hex() == "b10011065000140a0501000000007d4700"):
                    buttonPress = BTNBACK  # BACK
                if (resp.hex() == "b10011065000140a0510000000007d175f"):
                    buttonPress = BTNTICK  # TICK
                if (resp.hex() == "b10011065000140a0508000000007d3c7c"):
                    buttonPress = BTNUP  # UP
                if (resp.hex() == "b10010065000140a050200000000611d"):
                    buttonPress = BTNDOWN  # DOWN
                if (resp.hex() == "b10010065000140a0540000000006d67"):
                    buttonPress = BTNHELP   # HELP
                if (resp.hex() == "b10010065000140a0504000000002a68"):
                    buttonPress = BTNPLAY   # PLAY
            except:
                pass
            time.sleep(0.2)
            if buttonPress != 0:
                keycallback(buttonPress)
        time.sleep(0.05)

def subscribeEvents(keycallback, fieldcallback):
    # Called by any program wanting to subscribe to events
    # Arguments are firstly the callback function for key presses, secondly for piece lifts and places
    eventsthreadpointer = threading.Thread(target=eventsThread, args=([keycallback, fieldcallback]))
    eventsthreadpointer.daemon = True
    eventsthreadpointer.start()

def pauseEvents():
    global eventsrunning
    eventsrunning = 0
    time.sleep(0.5)

def unPauseEvents():
    global eventsrunning
    eventsrunning = 1

# poll()
# beep(SOUND_GENERAL)
# ledsOff()
# ledFromTo(0,63)
# while True:
#	poll()
# sys.exit()
