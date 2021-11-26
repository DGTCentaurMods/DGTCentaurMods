# Emulate the Millenium Chesslink protocol
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

from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper
from DGTCentaurMods.board import board

import time
import chess
import chess.engine
import serial
import sys
import pathlib
import threading
import psutil
import bluetooth
import subprocess
import select
import os
import bluetooth
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
	global server_sock
	print("Key event received: " + str(key))
	if key == gamemanager.BTNBACK:
		print("setting kill")
		kill = 1
		try:
			server_sock.close()
		except:
			pass
	if key == gamemanager.BTNPLAY:
		# Send the board state again (for cases where it doesn't seem to have sent)
		board.beep(board.SOUND_GENERAL)
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
		print("sending status on change")
		print(resp)
		sendMilleniumCommand(resp)

sendstatewithoutrequest = 1

def eventCallback(event):
	global curturn
	global engine
	global eloarg
	global kill
	global client_sock
	global sendstatewithoutrequest
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
		print("white turn event")
		epaper.writeText(0,"White turn")
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		print("black turn event")
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
	global client_sock
	global sendstatewithoutrequest
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
	print("sending status on change")
	sendMilleniumCommand(resp)

def pairThread():
	# Emulate bluetooth pairing by providing pairing in a separate thread too
	# First kill any running bt-agent, it may have been started from the menu
	for p in psutil.process_iter(attrs=['pid', 'name']):
		if "bt-agent" in p.info["name"]:
			p.kill()
			time.sleep(3)
	while True:
		print('running pair thread')
		# In case something has gone wrong we actually call bluetoothctl first to make it discoverable and pairable.
		p = subprocess.Popen(['/usr/bin/bluetoothctl'],stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, shell=True)
		poll_obj = select.poll()
		poll_obj.register(p.stdout, select.POLLIN)
		p.stdin.write("power on\n")
		p.stdin.flush()
		p.stdin.write("discoverable on\n")
		p.stdin.flush()
		p.stdin.write("pairable on\n")
		p.stdin.flush()
		time.sleep(4)
		p.terminate()
		p = subprocess.Popen(['/usr/bin/bt-agent --capability=NoInputNoOutput -p /etc/bluetooth/pin.conf'],stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
		poll_obj = select.poll()
		poll_obj.register(p.stdout, select.POLLIN)
		running = 1
		spamyes = 0
		spamtime = 0;
		while running == 1:
			poll_result = poll_obj.poll(0)
			if spamyes == 1:
				if time.time() - spamtime < 3:
					print("spamming yes!")
					p.stdin.write(b'yes\n')
					time.sleep(1)
				else:
					p.terminate()
					running = 0
			if poll_result and spamyes == 0:
				line = p.stdout.readline()
				if b'Device:' in line:
					print("detected device")
					p.stdin.write(b'yes\n')
					spamyes = 1
					spamtime = time.time()
			r = p.poll()
			if r is not None:
				running = 0
		time.sleep(0.1)

# Activate the epaper
epaper.initEpaper()
board.ledsOff()
epaper.writeText(0,'Connect remote')
epaper.writeText(1,'Device Now')
start = time.time()

pairThread = threading.Thread(target=pairThread, args=())
pairThread.daemon = True
pairThread.start()

# Kill rfcomm if it is started
os.system('sudo service rfcomm stop')
time.sleep(2)
for p in psutil.process_iter(attrs=['pid', 'name']):
	if str(p.info["name"]) == "rfcomm":
		p.kill()
iskilled = 0
print("checking killed")
while iskilled == 0:
	iskilled = 1
	for p in psutil.process_iter(attrs=['pid', 'name']):
		if str(p.info["name"]) == "rfcomm":
			iskilled = 0
	time.sleep(0.1)

kill = 0

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", bluetooth.PORT_ANY))
server_sock.settimeout(0.5)
server_sock.listen(1)
port = server_sock.getsockname()[1]
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
bluetooth.advertise_service(server_sock, "UARTClassicServer", service_id=uuid,
                            service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                            profiles=[bluetooth.SERIAL_PORT_PROFILE],
                            # protocols=[bluetooth.OBEX_UUID]
                            )

print("Waiting for connection on RFCOMM channel", port)
connected = 0
while connected == 0 and kill == 0:
	try:
		client_sock, client_info = server_sock.accept()
		connected = 1
	except:
		board.sendPacket(b'\x94', b'')
		expect = bytearray(b'\xb1\x00\x06' + board.addr1.to_bytes(1, byteorder='big') + board.addr2.to_bytes(1, byteorder='big'))
		resp = board.ser.read(10000)
		resp = bytearray(resp)
		if (resp != expect):
			if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
				# BACK BUTTON PRESSED
				kill = 1
		time.sleep(0.1)

# Subscribe to the game manager to activate the previous functions
if kill == 0:
	print("Accepted connection from", client_info)
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
	global client_sock
	global client_sock
	print("send command in")
	print(txt)
	cs = 0;
	tosend = bytearray(b'')
	for el in range(0,len(txt)):
		tosend.append(odd_par(ord(txt[el][0])))
		cs = cs ^ ord(txt[el][0])
	print("parityset")
	#h = str(hex(cs)).upper()
	h = "0x{:02x}".format(cs)
	h1 = h[2:3]
	h2 = h[3:4]
	print("checksum created")
	print(h)
	print(h1)
	print(h2)
	tosend.append(odd_par(ord(h1)))
	tosend.append(odd_par(ord(h2)))
	print("sending stuff")
	print(tosend.hex())
	print(str(tosend))
	#bt.write(tosend)
	#bt.flush()
	client_sock.send(bytes(tosend))
	#time.sleep(0.2)

while kill == 0:
	try:
		handled = 1
		while kill == 0:
			data = client_sock.recv(1)
			print(data)
			if not data:
				print("read failed")
				break
			cmd = data[0] & 127
			handled = 0
			print(cmd)
			print(chr(cmd))
			if chr(cmd) == 'V':
				# Remote is asking for the version
				# dump the checksum (two bytes represent the first and second characters in ascii of a hex
				# checksum made by binary xoring other stuff. weird!)
				client_sock.recv(2)
				sendMilleniumCommand("v3130")
				handled = 1
			if chr(cmd) == 'I':
				# Needed by chess.com app
				data = client_sock.recv(4)
				print("hit i")
				print(data.hex())
				print(data)
				sendMilleniumCommand("i0055mm\n")
				handled = 1
			if chr(cmd) == 'S':
				# Status - essentially asks for the board state to be sent
				client_sock.recv(2)
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
			if chr(cmd) == 'W':
				# Writes to E2ROM. (this allows setting of board scan response behaviour)
				h1 = client_sock.recv(1)[0] & 127
				h2 = client_sock.recv(1)[0] & 127
				hexn = '0x' + chr(h1) + chr(h2)
				address = int(str(hexn),16)
				h3 = client_sock.recv(1)[0] & 127
				h4 = client_sock.recv(1)[0] & 127
				hexn = '0x' + chr(h3) + chr(h4)
				value = int(str(hexn), 16)
				print(address)
				print(value)
				client_sock.recv(2)
				E2ROM[address] = value
				sendMilleniumCommand(str('w' + chr(h1) + chr(h2) + chr(h3) + chr(h4)))
				if address == 2 and (value & 0x01 == 1):
					sendstatewithoutrequest = 0
				handled = 1
			if chr(cmd) == 'X':
				# Extinguish all LEDs
				client_sock.recv(2)
				board.ledsOff()
				sendMilleniumCommand('x')
				handled = 1
			if chr(cmd) == 'R':
				# Reads from the E2ROM
				h1 = client_sock.recv(1)[0] & 127
				h2 = client_sock.recv(1)[0] & 127
				hexn = '0x' + chr(h1) + chr(h2)
				address = int(str(hexn), 16)
				value = E2ROM[address]
				h = str(hex(value)).upper()
				h3 = h[2:3]
				h4 = h[3:4]
				sendMilleniumCommand(str(chr(h1) + chr(2) + str(h3) + str(h4)))
				handled = 1
			if chr(cmd) == 'L':
				# We need to translate the lighting pattern. According to the spec the millenium board has 81 leds
				# This puts them on the corner of each square. Each byte represents a state in time slots so the
				# pattern uses 8 bits. But we need to translate this to the centaur's central light on the square
				# with it's regular flashing pattern.
				client_sock.recv(2) # Slot time
				mpattern = bytearray([0] * 81)
				moff = 0
				for x in range(0,81):
					h1 = client_sock.recv(1)[0] & 127
					h2 = client_sock.recv(1)[0] & 127
					hexn = '0x' + chr(h1) + chr(h2)
					v = int(str(hexn), 16)
					mpattern[moff] = v
					moff = moff + 1
				client_sock.recv(2) # Checksum
				centaurpattern = bytearray([0] * 64)
				ledmap = [
					[7, 8, 16, 17], [16, 17, 25, 26], [25, 26, 34, 35], [34, 35, 43, 44], [43, 44, 52, 53], [52, 53, 61, 62],
					[61, 62, 70, 71], [70, 71, 79, 80],
					[6, 7, 15, 16], [15, 16, 24, 25], [24, 25, 33, 34], [33, 34, 42, 43], [42, 43, 51, 52], [51, 52, 60, 61],
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
				tosend = bytearray(b'\xb0\x00\x0c' + board.addr1.to_bytes(1, byteorder='big') + board.addr2.to_bytes(1,byteorder='big') + b'\x05\x05\x00\x05')
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
				client_sock.recv(2)
				sendMilleniumCommand("t")
				sendstatewithoutrequest = 1
				time.sleep(3)
				handled = 1
			if handled == 0:
				print("unhandled")
				print(chr(cmd))
	except OSError:
		pass

	print("Disconnected.")

	client_sock.close()
	if kill == 0:
		print("Waiting for connection on RFCOMM channel", port)
		connected = 0
		while connected == 0 and kill == 0:
			try:
				client_sock, client_info = server_sock.accept()
				connected = 1
			except:
				try:
					board.sendPacket(b'\x94', b'')
					expect = bytearray(
						b'\xb1\x00\x06' + board.addr1.to_bytes(1, byteorder='big') + board.addr2.to_bytes(1,byteorder='big'))
					resp = board.ser.read(10000)
					resp = bytearray(resp)
					if (resp != expect):
						if (resp.hex() == "b10011065000140a0501000000007d4700"):
							# BACK BUTTON PRESSED
							kill = 1
				except:
					pass
				time.sleep(0.1)

server_sock.close()
os.system('sudo service rfcomm start')
time.sleep(2)

kill = 1
os._exit(0)

while True == False:
	print("true loop")
	kill = 0
	excount = 0
	while kill == 0:
		# In this loop we will do bluetooth reads
		cmd = 0
		handled = 1
		readsuccess = 0
		while readsuccess == 0 and kill == 0:
			try:
				data = bt.recv(1)
				cmd = data[0] & 127
				print(chr(cmd))
				handled = 0
				excount = 0
				readsuccess = 1
				time.sleep(0.1)
			except Exception as e:
				print("exception")
				print(e)
				#if bt.is_open == False:
				#	kill = 1
				#if not exists("/dev/rfcomm0"):
				#	kill = 1
				#pass
				excount = excount + 1
				time.sleep(0.5)
				if excount > 3:
					kill = 1

	bt.close()
	print(bt.is_open)
	print("killing rfcomm")
	for p in psutil.process_iter(attrs=['pid', 'name']):
		if str(p.info["name"]) == "rfcomm":
			p.kill()
	iskilled = 0
	print("checking killed")
	while iskilled == 0:
		iskilled = 1
		for p in psutil.process_iter(attrs=['pid', 'name']):
			if str(p.info["name"]) == "rfcomm":
				iskilled = 0
		time.sleep(0.1)
	print("is killed. restarting")
	#os.system('service rfcomm start')
	os.system('/usr/bin/rfcomm watch hci0 &')
	restarted = 0
	print("checking restart")
	while restarted == 0:
		for p in psutil.process_iter(attrs=['pid', 'name']):
			if str(p.info["name"]) == "rfcomm":
				print("found it")
				restarted = 1
		print("ran check")
		time.sleep(0.1)
	print("restarted")
	print("broke out")
	#time.sleep(1)
	while True:
		time.sleep(0.1)
		try:
			bt = serial.Serial("/dev/rfcomm0",baudrate=38400,timeout=60)
			break
		except:
			pass
	#time.sleep(3)
	print("new serial connection")
	print(bt.is_open)
