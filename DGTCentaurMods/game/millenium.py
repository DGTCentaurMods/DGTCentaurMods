# Emulate the Millenium Chesslink protocol
#
from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper
from DGTCentaurMods.board import board

import time
import chess
import chess.engine
import serial
import sys
import pathlib
from random import randint
from os.path import exists

curturn = 1
kill = 0
E2ROM = bytearray([0] * 256)

def keyCallback(key):
	# This function will receive any keys presses on the keys
	# under the display. Possibles:
	# gamemanager.BTNBACK  gamemanager.BTNTICK  gamemanager.BTNUP
	# gamemanager.BTNDOWN  gamemanager.BTNHELP  gamemanager.BTNPLAY
	global kill
	print("Key event received: " + str(key))
	if key == gamemanager.BTNBACK:
		kill = 1

def eventCallback(event):
	global curturn
	global engine
	global eloarg
	global kill
	global bt
	# This function receives event callbacks about the game in play
	if event == gamemanager.EVENT_NEW_GAME:
		epaper.writeText(0,"New Game")
		epaper.writeText(1,"               ")
		curturn = 1
		epaper.drawFen(gamemanager.cboard.fen())
		print("sending state")
		bs = gamemanager.cboard.fen()
		bs = bs.replace("/", "")
		bs = bs.replace("1", ".")
		bs = bs.replace("2", "..")
		bs = bs.replace("3", "...")
		bs = bs.replace("4", "....")
		bs = bs.replace("5", ".....")
		bs = bs.replace("6", "......")
		bs = bs.replace("7", ".......")
		bs = bs.replace("8", "........")
		resp = 's'
		for x in range(0, 64):
			resp = resp + bs[x]
		print(resp)
		sendMilleniumCommand(resp)
		board.ledsOff()
	if event == gamemanager.EVENT_WHITE_TURN:
		curturn = 1
		epaper.writeText(0,"White turn")
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		epaper.writeText(0,"Black turn")

	if type(event) == str:
		# Termination.CHECKMATE
		# Termination.STALEMATE
		# Termination.INSUFFICIENT_MATERIAL
		# Termination.SEVENTYFIVE_MOVES
		# Termination.FIVEFOLD_REPETITION
		# Termination.FIFTY_MOVES
		# Termination.THREEFOLD_REPETITION
		# Termination.VARIANT_WIN
		# Termination.VARIANT_LOSS
		# Termination.VARIANT_DRAW
		if event.startswith("Termination."):
			board.ledsOff()
			epaper.writeText(1,event[12:])
			time.sleep(10)
			kill = 1

def moveCallback(move):
	# This function receives valid moves made on the board
	# Note: the board state is in python-chess object gamemanager.cboard
	global bt
	epaper.drawFen(gamemanager.cboard.fen())
	epaper.writeText(9, move)
	# Note at the moment chess for android asks to send status on any change, but there are other options TODO
	bs = gamemanager.cboard.fen()
	bs = bs.replace("/", "")
	bs = bs.replace("1", ".")
	bs = bs.replace("2", "..")
	bs = bs.replace("3", "...")
	bs = bs.replace("4", "....")
	bs = bs.replace("5", ".....")
	bs = bs.replace("6", "......")
	bs = bs.replace("7", ".......")
	bs = bs.replace("8", "........")
	resp = 's'
	for x in range(0, 64):
		resp = resp + bs[x]
	sendMilleniumCommand(resp)

# Activate the epaper
epaper.initEpaper()
board.ledsOff()
epaper.writeText(0,'Connect remote')
epaper.writeText(1,'Device Now')
start = time.time()
#while exists("/dev/rfcomm0") == False and (time.time() - start < 30):
#	time.sleep(.01)

#bt = serial.Serial("/dev/rfcomm0",baudrate=38400)

while time.time() - start < 30:
	try:
		bt = serial.Serial("/dev/rfcomm0",baudrate=38400,timeout=60)
		time.sleep(2)
		break
	except:
		pass

if (time.time() - start >= 30):
	epaper.writeText(0,"TIMEOUT")
	epaper.writeText(1,"             ")
	time.sleep(2)
	sys.exit()
print("Connected")

# Subscribe to the game manager to activate the previous functions
gamemanager.subscribeGame(eventCallback, moveCallback, keyCallback)
epaper.writeText(0,"Place pieces in")
epaper.writeText(1,"Starting Pos")

def odd_par(b):
	byte = b & 127
	par = 1
	for _ in range(7):
		bit = byte & 1
		byte = byte >> 1
		par = par ^ bit
	if par == 1:
		byte = b | 128
	else:
		byte = b & 127
	return byte

def sendMilleniumCommand(txt):
	global bt
	cs = 0;
	tosend = bytearray(b'')
	for el in range(0,len(txt)):
		tosend.append(odd_par(ord(txt[el][0])))
		cs = cs ^ ord(txt[el][0])
	h = str(hex(cs)).upper()
	h1 = h[2:3]
	h2 = h[3:4]
	tosend.append(odd_par(ord(h1)))
	tosend.append(odd_par(ord(h2)))
	#print(tosend)
	bt.write(tosend)


while kill == 0:
	# In this loop we will do bluetooth reads
	cmd = 0
	handled = 1
	try:
		data = bt.read(1)
		cmd = data[0] & 127
		handled = 0
	except serial.serialutil.SerialException:
		if bt.is_open == False:
			kill = 1
		if not exists("/dev/rfcomm0"):
			kill = 1
		pass

	if chr(cmd) == 'V':
		# Remote is asking for the version
		# dump the checksum (two bytes represent the first and second characters in ascii of a hex
		# checksum made by binary xoring other stuff. weird!)
		bt.read(2)
		sendMilleniumCommand("v3130")
		handled = 1
	if chr(cmd) == 'I':
		# Chess.com app is sending this but I can't find info on what it is!
		bt.read(4)
		print("hit i")
		sendMilleniumCommand("i00")
	if chr(cmd) == 'X':
		# Extinguish all LEDs
		bt.read(2)
		board.ledsOff()
		sendMilleniumCommand('x')
		handled = 1
	if chr(cmd) == 'W':
		# Writes to E2ROM. (this allows setting of board scan response behaviour)
		h1 = bt.read(1)[0] & 127
		h2 = bt.read(1)[0] & 127
		hexn = '0x' + chr(h1) + chr(h2)
		address = int(str(hexn),16)
		h3 = bt.read(1)[0] & 127
		h4 = bt.read(1)[0] & 127
		hexn = '0x' + chr(h3) + chr(h4)
		value = int(str(hexn), 16)
		#print(address)
		#print(value)
		bt.read(2)
		E2ROM[address] = value
		sendMilleniumCommand(str('w' + chr(h1) + chr(h2) + chr(h3) + chr(h4)))
		handled = 1
	if chr(cmd) == 'R':
		# Reads from the E2ROM
		h1 = bt.read(1)[0] & 127
		h2 = bt.read(1)[0] & 127
		hexn = '0x' + chr(h1) + chr(h2)
		address = int(str(hexn), 16)
		value = E2ROM[address]
		h = str(hex(value)).upper()
		h3 = h[2:3]
		h4 = h[3:4]
		sendMilleniumCommand(str(chr(h1) + chr(2) + str(h3) + str(h4)))
		handled = 1
	if chr(cmd) == 'S':
		# Status - essentially asks for the board state to be sent
		bt.read(2)
		bs = gamemanager.cboard.fen()
		bs = bs.replace("/","")
		bs = bs.replace("1",".")
		bs = bs.replace("2", "..")
		bs = bs.replace("3", "...")
		bs = bs.replace("4", "....")
		bs = bs.replace("5", ".....")
		bs = bs.replace("6", "......")
		bs = bs.replace("7", ".......")
		bs = bs.replace("8", "........")
		resp = 's'
		for x in range(0,64):
			resp = resp + bs[x]
		sendMilleniumCommand(resp)
		handled = 1
	if chr(cmd) == 'L':
		# We need to translate the lighting pattern. According to the spec the millenium board has 81 leds
		# This puts them on the corner of each square. Each byte represents a state in time slots so the
		# pattern uses 8 bits. But we need to translate this to the centaur's central light on the square
		# with it's regular flashing pattern.
		bt.read(2) # Slot time
		mpattern = bytearray([0] * 81)
		moff = 0
		for x in range(0,81):
			h1 = bt.read(1)[0] & 127
			h2 = bt.read(1)[0] & 127
			hexn = '0x' + chr(h1) + chr(h2)
			v = int(str(hexn), 16)
			mpattern[moff] = v
			moff = moff + 1
		bt.read(2) # Checksum
		centaurpattern = bytearray([0] * 64)
		ledmap = [
			[7, 8, 16, 17], [16, 17, 25, 26], [26, 27, 34, 35], [34, 35, 43, 44], [43, 44, 52, 53], [52, 53, 61, 62],
			[61, 62, 70, 71], [70, 71, 79, 80],
			[6, 7, 15, 16], [15, 16, 24, 25], [24, 25, 33, 34], [34, 35, 42, 43], [42, 43, 51, 52], [51, 52, 60, 61],
			[60, 61, 69, 70], [69, 70, 78, 79],
			[5, 6, 14, 15], [14, 15, 23, 24], [23, 24, 32, 33], [32, 33, 41, 42], [41, 42, 50, 51], [50, 51, 59, 60],
			[59, 60, 68, 69], [68, 69, 77, 78],
			[4, 5, 13, 14], [13, 14, 22, 23], [22, 23, 31, 32], [31, 32, 40, 41], [40, 41, 49, 50], [49, 50, 58, 59],
			[58, 59, 67, 68], [67, 68, 76, 77],
			[3, 4, 12, 13], [12, 13, 21, 22], [21, 22, 30, 31], [30, 31, 39, 40], [39, 40, 48, 49], [48, 49, 57, 58],
			[57, 58, 66, 67], [66, 67, 75, 76],
			[2, 3, 11, 12], [11, 12, 20, 21], [20, 21, 29, 30], [29, 30, 38, 39], [38, 39, 47, 48], [47, 48, 56, 57],
			[56, 57, 65, 66], [65, 66, 74, 75],
			[1, 2, 10, 11], [10, 11, 19, 20], [19, 20, 28, 29], [28, 29, 37, 38], [37, 38, 46, 47], [46, 47, 55, 56],
			[55, 56, 64, 65], [64, 65, 73, 74],
			[0, 1, 9, 10], [9, 10, 18, 19], [18, 19, 27, 28], [27, 28, 36, 37], [36, 37, 45, 46], [45, 46, 54, 55],
			[54, 55, 63, 64], [63, 64, 72, 73]
		]
		for x in range(0, 64):
			lmap = ledmap[x];
			if mpattern[lmap[0]] > 0:
				centaurpattern[x] = centaurpattern[x] + 1
			if mpattern[lmap[1]] > 0:
				centaurpattern[x] = centaurpattern[x] + 1
			if mpattern[lmap[2]] > 0:
				centaurpattern[x] = centaurpattern[x] + 1
			if mpattern[lmap[3]] > 0:
				centaurpattern[x] = centaurpattern[x] + 1
		# Now take only the squares where all lights are light
		for x in range(0, 64):
			if centaurpattern[x] != 4:
				centaurpattern[x] = 0
		# If a piece has moved 2 squares then we need to elimate the middle LED
		for r in range(0, 8):
			for t in range(0, 6):
				if centaurpattern[(r * 8) + t] == 4 and centaurpattern[(r * 8) + (t + 1)] == 4 and centaurpattern[
					(r * 8) + (t + 2)] == 4:
					centaurpattern[(r * 8) + (t + 1)] = 0
		for r in range(0, 6):
			for t in range(0, 8):
				if centaurpattern[(r * 8) + t] == 4 and centaurpattern[((r + 1) * 8) + t] == 4 and centaurpattern[
					((r + 2) * 8) + t] == 4:
					centaurpattern[((r + 1) * 8) + t] = 0
		board.ledsOff()
		trigger = 0
		tosend = bytearray(b'\xb0\x00\x0c\x06\x50\x05\x05\x00\x05')
		for x in range(0, 64):
			if centaurpattern[x] > 0:
				trigger = 1
				tosend.append(board.rotateField(x))
		if trigger == 1:
			tosend[2] = len(tosend) + 1
			tosend.append(board.checksum(tosend))
			board.ser.write(tosend)
		sendMilleniumCommand("l")
		handled = 1
	if chr(cmd) == 'T':
		# Reset. Just sleep for a bit :)
		bt.read(2)
		sendMilleniumCommand("t")
		time.sleep(3)
		handled = 1

	if handled == 0:
		print(chr(cmd))

	time.sleep(0.1)