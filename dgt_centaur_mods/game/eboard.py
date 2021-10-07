# An attempt to emulate the DGT e-board protocol
#
# Ed Nekebno
#
# Pair first
# Connect after the chessboard displays
#
# TODO
# Castling - move king and then rook works in chess for android, but not whitepawn

import serial
import time
from os.path import exists
from dgt_centaur_mods.board import boardfunctions
import threading

# https://github.com/well69/picochess-1/blob/master/test/dgtbrd-ruud.h
DGT_SEND_RESET = 0x40 # Puts the board into IDLE mode, cancelling any UPDATE mode
DGT_TO_BUSMODE = 0x4a
DGT_STARTBOOTLOADER = 0x4e
DGT_TRADEMARK = 0x12
DGT_RETURN_SERIALNR = 0x45
DGT_SERIALNR = 0x11
DGT_RETURN_LONG_SERIALNR = 0x55
DGT_LONG_SERIALNR = 0x22
DGT_SEND_CLK = 0x41
DGT_BWTIME = 0x0d

MESSAGE_BIT = 0x80

DGT_BUSADRES = 0x10
DGT_TO_BUSMODE = 0x4a
DGT_SEND_VERSION = 0x4d
DGT_VERSION = 0x13
DGT_SEND_BRD = 0x42
DGT_BOARD_DUMP = 0x06
DGT_SEND_UPDATE = 0x43
DGT_SEND_UPDATE_BRD = 0x44
DGT_FIELD_UPDATE = 0x0e
DGT_SEND_UPDATE_NICE = 0x4b
DGT_SET_LEDS = 0x60
DGT_CLOCK_MESSAGE = 0x2b

DGT_SEND_BATTERY_STATUS = 0x4c
DGT_BATTERY_STATUS = 0x20

DGT_BUS_PING = 0x87
DGT_MSG_BUS_PING = 0x07

DGT_RETURN_BUSADRES = 0x46
DGT_SEND_TRADEMARK = 0x47


EMPTY = 0x00
WPAWN = 0x01
WROOK = 0x02
WKNIGHT = 0x03
WBISHOP = 0x04
WKING = 0x05
WQUEEN = 0x06
BPAWN = 0x07
BROOK = 0x08
BKNIGHT = 0x09
BBISHOP = 0x0a
BKING = 0x0b
BQUEEN = 0x0c
PIECE1 = 0x0d  # Magic piece: Draw
PIECE2 = 0x0e  # Magic piece: White win
PIECE3 = 0x0f  # Magic piece: Black win
board = bytearray([EMPTY] * 64)
litsquares = []
startstate = bytearray(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01')

boardfunctions.initScreen()

if bytearray(boardfunctions.getBoardState()) != startstate:
	boardfunctions.writeText(0,'Place pieces')
	boardfunctions.writeText(1,'in startpos')
	# As the centaur can light up squares - let's use the
	# squares to help people out
	while bytearray(boardfunctions.getBoardState()) != startstate:
		rstate = boardfunctions.getBoardState()
		tosend = bytearray(b'\xb0\x00\x0c\x06\x50\x05\x12\x00\x05')
		# '\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x37\x36\x35\x34\x33\x32\x31\x30\x0d')
		for x in range(0, 64):
			if x < 16 or x > 47:
				if rstate[x] != 1:
					tosend.append(x)
			if x > 15 and x < 48:
				if rstate[x] == 1:
					tosend.append(x)
		tosend[2] = len(tosend) + 1
		tosend.append(boardfunctions.checksum(tosend))
		boardfunctions.ser.write(tosend)
		time.sleep(0.5)
	boardfunctions.ledsOff()

# As we can only detect piece presence on the centaur and not pieces, we must have a known start state
print("Setup board")
while bytearray(boardfunctions.getBoardState()) != startstate:
	time.sleep(0.5)
board[7] = WROOK
board[6] = WKNIGHT
board[5] = WBISHOP
board[4] = WQUEEN
board[3] = WKING
board[2] = WBISHOP
board[1] = WKNIGHT
board[0] = WROOK
board[15] = WPAWN
board[14] = WPAWN
board[13] = WPAWN
board[12] = WPAWN
board[11] = WPAWN
board[10] = WPAWN
board[9] = WPAWN
board[8] = WPAWN
board[55] = BPAWN
board[54] = BPAWN
board[53] = BPAWN
board[52] = BPAWN
board[51] = BPAWN
board[50] = BPAWN
board[49] = BPAWN
board[48] = BPAWN
board[63] = BROOK
board[62] = BKNIGHT
board[61] = BBISHOP
board[60] = BQUEEN
board[59] = BKING
board[58] = BBISHOP
board[57] = BKNIGHT
board[56] = BROOK
print("board is setup")

boardfunctions.clearScreen()

def drawCurrentBoard():
	global board
	pieces = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	for q in range(0,64):
		squarerow = (q // 8)
		squarecol = (q % 8)
		squarerow = squarerow
		squarecol = 7 - squarecol
		field = (squarerow * 8) + squarecol
		pieces[field] = board[q]
	for x in range(0,64):
		if pieces[x] == WPAWN:
			pieces[x]='P'
		if pieces[x] == BPAWN:
			pieces[x]='p'
		if pieces[x] == WROOK:
			pieces[x]='R'
		if pieces[x] == BROOK:
			pieces[x]='r'
		if pieces[x] == WBISHOP:
			pieces[x]='B'
		if pieces[x] == BBISHOP:
			pieces[x]='b'
		if pieces[x] == WKNIGHT:
			pieces[x]='N'
		if pieces[x] == BKNIGHT:
			pieces[x]='n'
		if pieces[x] == WQUEEN:
			pieces[x]='Q'
		if pieces[x] == BQUEEN:
			pieces[x]='q'
		if pieces[x] == WKING:
			pieces[x]='K'
		if pieces[x] == BKING:
			pieces[x]='k'
		if pieces[x] == EMPTY:
			pieces[x]=' '
	boardfunctions.drawBoard(pieces)

boardtoscreen = 0

def screenUpdate():
	# Separate thread to display the screen/pieces should improve
	# responsiveness
	global board
	global boardtoscreen
	while True:
		time.sleep(2)
		if boardtoscreen == 1:
			drawCurrentBoard()

def pieceMoveDetectionThread():
	# Separate thread to take care of detecting piece movement
	# for the board, so that it isn't waiting on the bluetooth
	# read from the other end
	global bt
	global sendupdates
	global timer
	global WROOK,WBISHOP,WKNIGHT,WQUEEN,WKING,WPAWN,BROOK,BBISHOP,BKNIGHT,BQUEEN,BKING,BPAWN,EMPTY
	global board
	global curturn
	global boardtoscreen
	lastlift = 0
	kinglift = 0
	lastfield = -1
	castlemode = 0
	while True:
		time.sleep(0.05)
		if sendupdates == 1:
			boardtoscreen = 1
			boardfunctions.ser.read(10000)
			tosend = bytearray(b'\x83\x06\x50\x59')
			boardfunctions.ser.write(tosend)
			expect = bytearray(b'\x85\x00\x06\x06\x50\x61')
			resp = boardfunctions.ser.read(1000)
			resp = bytearray(resp)
			if (bytearray(resp) != expect):
				if (resp[0] == 133 and resp[1] == 0):
					for x in range(0, len(resp) - 1):
						if (resp[x] == 64):
							# A piece has been lifted
							fieldHex = resp[x + 1]
							squarerow = (fieldHex // 8)
							squarecol = (fieldHex % 8)
							squarerow = 7 - squarerow
							squarecol = 7 - squarecol
							field = (squarerow * 8) + squarecol
							print("UP: " + str(field))
							if curturn == 1:
								# white
								item = board[field]
								if (item == WROOK or item == WBISHOP or item == WKNIGHT or item == WQUEEN or item == WKING or item == WPAWN):
									lastlift = board[field]
							if curturn == 0:
								#black
								item = board[field]
								if (item == BROOK or item == BBISHOP or item == BKNIGHT or item == BQUEEN or item == BKING or item == BPAWN):
									lastlift = board[field]
							print(lastlift)
							board[field] = EMPTY
							tosend = bytearray(b'')
							tosend.append(DGT_FIELD_UPDATE | MESSAGE_BIT)
							tosend.append(0)
							tosend.append(5)
							tosend.append(field)
							tosend.append(EMPTY)
							bt.write(tosend)
							bt.write(tosend)
							bt.write(tosend)
							if item == WKING or item == BKING:
								if field == 3 or field == 59:
									# This is a king lift that could be part of castling.
									print("kinglift")
									kinglift = 1
							else:
								kinglift = 0
							lastfield = field
						if (resp[x] == 65):
							# A piece has been placed
							fieldHex = resp[x + 1]
							squarerow = (fieldHex // 8)
							squarecol = (fieldHex % 8)
							squarerow = 7 - squarerow
							squarecol = 7 - squarecol
							field = (squarerow * 8) + squarecol
							print("DOWN: " + str(field))
							print(lastlift)
							board[field] = lastlift
							tosend = bytearray(b'')
							tosend.append(DGT_FIELD_UPDATE | MESSAGE_BIT)
							tosend.append(0)
							tosend.append(5)
							tosend.append(field)
							tosend.append(lastlift)
							bt.write(tosend)
							bt.write(tosend)
							bt.write(tosend)
							boardfunctions.beep(boardfunctions.SOUND_GENERAL)
							if curturn == 1:
								# white
								if lastlift != EMPTY:
									curturn = 0
							else:
								#black
								if lastlift != EMPTY:
									curturn = 1
							# If kinglift is 1 and lastfield is 3 or 59 then if the king has moved to
							# 1 or 5 or 61 or 57 then the user is going to move the rook next
							if kinglift == 1:
								if lastfield == 3 or lastfield == 59:
									if field == 1 or field == 5 or field == 61 or field == 57:
										print("Castle attempt detected")
										if curturn == 0:
											curturn = 1
										else:
											curturn = 0
							kinglift = 0
							lastfield = field
			tosend = bytearray(b'\x94\x06\x50\x6a')
			boardfunctions.ser.write(tosend)
			resp = boardfunctions.ser.read(1000)

			timer = timer + 1
			if timer > 50:
				if bytearray(boardfunctions.getBoardState()) == startstate:
					board = bytearray([EMPTY] * 64)
					board[7] = WROOK
					board[6] = WKNIGHT
					board[5] = WBISHOP
					board[4] = WQUEEN
					board[3] = WKING
					board[2] = WBISHOP
					board[1] = WKNIGHT
					board[0] = WROOK
					board[15] = WPAWN
					board[14] = WPAWN
					board[13] = WPAWN
					board[12] = WPAWN
					board[11] = WPAWN
					board[10] = WPAWN
					board[9] = WPAWN
					board[8] = WPAWN
					board[55] = BPAWN
					board[54] = BPAWN
					board[53] = BPAWN
					board[52] = BPAWN
					board[51] = BPAWN
					board[50] = BPAWN
					board[49] = BPAWN
					board[48] = BPAWN
					board[63] = BROOK
					board[62] = BKNIGHT
					board[61] = BBISHOP
					board[60] = BQUEEN
					board[59] = BKING
					board[58] = BBISHOP
					board[57] = BKNIGHT
					board[56] = BROOK
					for x in range(0,64):
						tosend = bytearray(b'')
						tosend.append(DGT_FIELD_UPDATE | MESSAGE_BIT)
						tosend.append(0)
						tosend.append(5)
						tosend.append(x)
						tosend.append(board[x])
						bt.write(tosend)
						bt.flushOutput()
			if timer > 50:
				timer = 0



drawCurrentBoard()
boardfunctions.writeText(0,'Connect remote')
boardfunctions.writeText(1,'Device Now')

while exists("/dev/rfcomm0") == False:
	time.sleep(.01)

print("Connected")

bt= serial.Serial("/dev/rfcomm0",baudrate=115200, timeout=10)
boardfunctions.clearScreen()
boardfunctions.writeText(0,'Connected')
boardfunctions.writeText(1,'         ')
print("start")

scrUpd = threading.Thread(target=screenUpdate, args=())
scrUpd.daemon = True
scrUpd.start()

sendupdates = 0
timer = 0
# 0 for black, 1 for white
curturn = 1

pMove = threading.Thread(target=pieceMoveDetectionThread,args=())
pMove.daemon = True
pMove.start()

# Clear any remaining data sent from the board
boardfunctions.clearBoardData()


lastlift = EMPTY

while True:
	data=bt.read(1)

	if len(data) > 0:
		handled = 0
		if data[0] == DGT_SEND_RESET:
			# Puts the board in IDLE mode
			#boardfunctions.clearBoardData()
			#boardfunctions.writeText(0, 'Init')
			#boardfunctions.writeText(1, '         ')
			handled = 1
		if data[0] == DGT_TO_BUSMODE:
			# Puts the board in BUS mode
			handled = 1
		if data[0] == DGT_RETURN_BUSADRES:
			tosend = bytearray(b'\x00\x00\x05\x08\x01')
			tosend[0] = DGT_BUSADRES | MESSAGE_BIT
			bt.write(tosend)
			bt.flushOutput()
			sentbus = 1
			handled = 1
		if data[0] == DGT_SEND_TRADEMARK:
			# Send DGT Trademark Message
			tosend = bytearray(b'\x00\x00\x00\x00\x00')
			tosend[0] = DGT_TRADEMARK | MESSAGE_BIT
			tosend[1] = 0
			tosend[2] = 5
			tosend[3] = ord('T')
			tosend[4] = ord('M')
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_BUS_PING:
			# Received a ping message
			# The message actually has two more bytes and a checksum
			dump = bt.read(3)
			tosend = bytearray(b'')
			tosend.append(DGT_MSG_BUS_PING | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(5)
			tosend.append(8)
			tosend.append(1)
			time.sleep(0.5)
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_RETURN_SERIALNR:
			# Return our serial number
			tosend = bytearray(b'')
			tosend.append(DGT_SERIALNR | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(8)
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			bt.write(tosend)
			bt.flushOutput()
			bt.write(tosend)
			bt.flushOutput()
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_RETURN_LONG_SERIALNR:
			# Return our long serial number
			tosend = bytearray(b'')
			tosend.append(DGT_LONG_SERIALNR | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(13)
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			tosend.append(ord('1'))
			bt.write(tosend)
			bt.flushOutput()
			bt.write(tosend)
			bt.flushOutput()
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_SEND_VERSION:
			# Return our serial number
			tosend = bytearray(b'')
			tosend.append(DGT_VERSION | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(5)
			tosend.append(1)
			tosend.append(0)
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_SEND_BRD:
			# Send the board
			tosend = bytearray(b'')
			tosend.append(DGT_BOARD_DUMP | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(67)
			for x in range(0,64):
				tosend.append(board[x])
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_SET_LEDS:
			# LEDs! Not sure about this code, but at the moment it works with Chess for Android
			# Note the mapping for the centaur goes 0 (a1) to 63 (h8)
			# This mapping goes 0 (h1) to 63 (a8)
			dd = bt.read(5)
			print(dd.hex())
			if dd[1] == 0:
				# Off
				print("off")
				squarerow = 7 - (dd[2] // 8)
				squarecol = 7 - (dd[2] % 8)
				froms = (squarerow * 8) + squarecol
				squarerow = 7 - (dd[3] // 8)
				squarecol = 7 - (dd[3] % 8)
				tos = (squarerow * 8) + squarecol
				litsquares = list(filter(lambda a: a != froms, litsquares))
				litsquares = list(filter(lambda a: a != tos, litsquares))
				if dd[2] == 0 and dd[3] == 63:
					# This seems to be some code to turn the lights off
					litsquares = []
					boardfunctions.ledsOff()
				print(len(litsquares))
				if len(litsquares) > 0:
					tosend = bytearray(b'\xb0\x00\x0b\x06\x50\x05\x08\x00\x05')
					# '\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x37\x36\x35\x34\x33\x32\x31\x30\x0d')
					for x in range(0, len(litsquares)):
						tosend.append(litsquares[x])
					tosend[2] = len(tosend) + 1
					tosend.append(boardfunctions.checksum(tosend))
					boardfunctions.ser.write(tosend)
				else:
					boardfunctions.ledsOff()
			if dd[1] == 1:
				# On
				print("on")
				squarerow = 7 - (dd[2] // 8)
				squarecol = 7 - (dd[2] % 8)
				froms = (squarerow * 8) + squarecol
				squarerow = 7 - (dd[3] // 8)
				squarecol = 7 - (dd[3] % 8)
				tos = (squarerow * 8) + squarecol
				litsquares.append(froms)
				litsquares.append(tos)
				tosend = bytearray(b'\xb0\x00\x0b\x06\x50\x05\x08\x00\x05')
				# '\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x37\x36\x35\x34\x33\x32\x31\x30\x0d')
				for x in range(0, len(litsquares) - 1):
					tosend.append(litsquares[x])
				tosend[2] = len(tosend) + 1
				tosend.append(boardfunctions.checksum(tosend))
				boardfunctions.ser.write(tosend)
			handled = 1
		if data[0] == DGT_CLOCK_MESSAGE:
			# For now don't display the clock, maybe later. But the other device acts as it
			# Just drop the data
			sz = bt.read(1)
			sz = sz[0]
			d = bt.read(sz)
			handled = 1
		if data[0] == DGT_SEND_UPDATE or data[0] == DGT_SEND_UPDATE_BRD:
			# Send an update
			tosend = bytearray(b'')
			tosend.append(DGT_FIELD_UPDATE | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(5)
			tosend.append(0)
			tosend.append(board[0])
			bt.write(tosend)
			bt.flushOutput()
			#boardfunctions.writeText(0, 'PLAY   ')
			#boardfunctions.writeText(1, '         ')
			# Here let's actually loop through reading the board states
			sendupdates = 1
			handled = 1
		if data[0] == DGT_SEND_UPDATE_NICE:
			# Implementing this at the moment upsets RabbitPlugin :(
			#boardfunctions.writeText(0, 'PLAY   ')
			#boardfunctions.writeText(1, '         ')
			#sendupdates = 1
			handled = 1
		if data[0] == DGT_SEND_CLK:
			# RabbitPlugin doesn't work without this so let's fake this for now
			tosend = bytearray(DGT_BWTIME | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(10)
			tosend.append(7)
			tosend.append(0)
			tosend.append(0)
			tosend.append(7)
			tosend.append(0)
			tosend.append(0)
			tosend.append(0)
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if data[0] == DGT_SEND_BATTERY_STATUS:
			# Ideally in the future we'll put a function in boardfunctions to get the
			# battery status from the centaur. But for now, fake it!
			tosend = bytearray(b'')
			tosend.append(DGT_BATTERY_STATUS | MESSAGE_BIT)
			tosend.append(0)
			tosend.append(12)
			tosend.append(100) # 100%
			tosend.append(0x7f)
			tosend.append(0x7f)
			tosend.append(0)
			tosend.append(0)
			tosend.append(0)
			tosend.append(0)
			tosend.append(0)
			tosend.append(0)
			bt.write(tosend)
			bt.flushOutput()
			handled = 1
		if handled == 0:
			print("Unhandled message type: " + data.hex())