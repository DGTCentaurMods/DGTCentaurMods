# Play a game on lichess
#
# This is the second version of this script, it uses gamemanager to ensure that the system
# gets all the benefits + any future upgrades.
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
import datetime
import gc
import os
import pathlib
import ssl
import sys
import threading
import time
from random import randint

import berserk
import chess
import chess.engine
from DGTCentaurMods.board import board, centaur
from DGTCentaurMods.display import epaper
from DGTCentaurMods.game import gamemanager

import logging
logging.basicConfig(level=logging.INFO)

logging.info("loaded lichess.py")
curturn = 1
computeronturn = 0
kill = 0
who = None
player = None
remotemoves = ""
lastremotemoves = "1234"
lastmove = "1234"

def keyCallback(key):
	# This function will receive any keys presses on the keys
	# under the display. Possibles:
	# gamemanager.BTNBACK  gamemanager.BTNTICK  gamemanager.BTNUP
	# gamemanager.BTNDOWN  gamemanager.BTNHELP  gamemanager.BTNPLAY
	global kill
	print("Key event received: " + str(key))
	if key == gamemanager.BTNBACK:
		kill = 1

def makeAPIMove():
	global lastmove
	global remotemoves
	global lastremotemoves
	# Wait for a remote move to come in
	while lastremotemoves == remotemoves:
		time.sleep(0.1)
	# Then wait for one that is not lastmove
	while lastmove == str(remotemoves)[-5:].replace("\"", "").replace("'","").replace(" ", "").lower():
		time.sleep(0.1)
	curmove = str(remotemoves)[-5:].replace("\"", "").replace("'","").replace(" ", "").lower()
	gamemanager.computerMove(curmove)
	lastremotemoves = remotemoves
	lastmove = curmove

def eventCallback(event):
	global curturn
	global engine
	global eloarg
	global kill
	global playeriswhite
	global gameid
	# This function receives event callbacks about the game in play
	if event == gamemanager.EVENT_NEW_GAME:
		epaper.writeText(0,"New Game")
		curturn = 1
		epaper.drawFen(gamemanager.cboard.fen(),3)
		epaper.writeText(10, whiteplayer)
		epaper.writeText(11, ("(" + whiterating.replace("None", "") + ")").replace("()",""))
		epaper.writeText(1, blackplayer)
		epaper.writeText(2, ("(" + blackrating.replace("None", "") + ")").replace("()",""))
		if playeriswhite == 1:
			# If it is the player's turn
			epaper.writeText(12,"Your turn       ")
		else:
			# Otherwise if it is the lichess player's turn
			epaper.writeText(12,"Opponent turn   ")
	if event == gamemanager.EVENT_WHITE_TURN:
		curturn = 1
		epaper.writeText(0,"White turn")
		if playeriswhite == 1:
			# If it is the player's turn
			epaper.writeText(12,"Your turn       ")
		else:
			# Otherwise if it is the lichess player's turn
			epaper.writeText(12,"Opponent turn   ")
			makeAPIMove()
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		epaper.writeText(0,"Black turn")
		if playeriswhite == 0:
			# If it is the player's turn
			epaper.writeText(12,"Your turn       ")
		else:
			# Otherwise if it is the lichess player's turn
			epaper.writeText(12,"Opponent turn   ")
			makeAPIMove()
	if event == gamemanager.EVENT_RESIGN_GAME:
		client.board.resign_game(gameid)
		if playeriswhite == 1:
			gamemanager.resignGame(1)
		else:
			gamemanager.resignGame(2)
	if event == gamemanager.EVENT_REQUEST_DRAW:
		client.board.offer_draw(gameid)

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
			epaper.writeText(0,event[12:])
			time.sleep(10)
			kill = 1

def moveCallback(move):
	# This function receives valid moves made on the board
	# Note: the board state is in python-chess object gamemanager.cboard
	global whiteplayer
	global curturn
	global playeriswhite
	global lastmove
	epaper.drawFen(gamemanager.cboard.fen(),3)
	# As long as we have player data we have a connection to the lichess api
	# so send the move if it's our turn
	print("make move called")
	if whiteplayer != "":
		print("white player name is set")
		if (curturn == 1 and playeriswhite == 1) or (curturn == 0 and playeriswhite == 0):
			print("making move")
			ret = False
			while ret == False:
				ret = client.board.make_move(gameid, move)
				if ret == False:
					print("api failed to respond, trying again")
					time.sleep(1)
			lastmove = str(move).lower()
			print(ret)


# Activate the epaper
epaper.initEpaper()

# Get the token
token = centaur.get_lichess_api()
if (token == "" or token == "tokenhere") and kill == 0:
	print('no token')
	epaper.writeText(0,"No API token      ")
	epaper.writeText(1,"Fill it in       ")
	epaper.writeText(2,"in the web")
	epaper.writeText(3,"interface")
	time.sleep(10)
	kill = 1
	sys.exit()

# This script has a calling pattern. 'current' for the currently running game
# or New [time=10|15|30|60] [increment=5|10|20] [rated=True|False] [color=White|Black|Random]

if (len(sys.argv) == 1) and kill == 0:
	logging.error("no parameter given!")
	epaper.writeText(0,"Error:        ")
	epaper.writeText(1,"lichess.py    ")
	epaper.writeText(2,"no parameter")
	epaper.writeText(3,"given!")
	time.sleep(10)
	kill = 1
	sys.exit()

if (len(sys.argv) > 1) and kill == 0:
	if sys.argv[1] not in ["New", "Ongoing", "Challenge"]:
		logging.error("Wrong first input parameter")
		sys.exit()

gtime = 0
ginc = 0
grated = 0
gcolor = 0
gameid = ""
ongoing = False
challenge = False
if len(sys.argv) > 1:
	if sys.argv[1] == "New":
		gtime = sys.argv[2]
		ginc = sys.argv[3]
		grated = sys.argv[4]
		gcolor = sys.argv[5]
	elif sys.argv[1] == "Ongoing":
		ongoing = True
		gameid = sys.argv[2]
	elif sys.argv[1] == "Challenge":
		challenge = True
		challengeid = sys.argv[2]
		challenge_direction = sys.argv[3]
	else:
		logging.error("Wrong input value")
		raise ValueError("Not expected value %s" % (sys.argv[1],))

# Prepare for the lichess api
session = berserk.TokenSession(token)
client = berserk.Client(session=session)

# Get this user's details
try:
	who = client.account.get()
	player = str(who.get('username'))
except:
	print('no token')
	epaper.writeText(0,"Error in API token")
	epaper.writeText(1,"                 ")
	time.sleep(10)
	kill = 1
	sys.exit()

print(who)
print(player)

def newGameThread():
	# Starts a new game and monitors client.board.stream_incoming events
	# in the original I had a time.sleep(5) here first, not sure why
	global gtime
	global ginc
	global grated
	global gcolor
	ratingrange = centaur.lichess_range
	epaper.writeText(0, "Finding Game...")
	# not sure if there was a reason this was a bunch of ifs
	# Simplified it to a single call
	seek_rated = True if grated == "True" else False
	client.board.seek(int(gtime), int(ginc), seek_rated, color=gcolor, rating_range=f'{ratingrange}')
	

def newChallengeThread():
	global challengeid
	global gameid
	epaper.writeText(0, "Accepting challenge / waiting for the opponent...")
	logging.debug("Accepting challenge / waiting for the opponent...")
	if challenge_direction == 'in':
		client.challenges.accept(challengeid)
	else:
		# wait until challenge accepted?
		...

	gameid = challengeid


#def ongoingGameThread():
	#global ongoing
	#global gameid
	#if not ongoing:
	#	raise ValueError("Value `ongoing` is expected to be True")
	#epaper.writeText(0, "Waiting fot the game...")
	#logging.info("Waiting fot the game...")
	#while True:
	#	current_games = client.games.get_ongoing(10)
	#	if len(current_games) > 0:
	#		break
	#	time.sleep(0.5)
	#gameid = sys.argv[2]
	#logging.info("found game with ID="+gameid)


checkback = 0
kill = 0

def backTest():
	# Check for the back button. We use this to allow the user to stop seeking for a game
	global kill
	global checkback
	global gameid
	while checkback == 0:
		try:
			board.sendPacket(b'\x94', b'')
			resp = board.ser.read(10000)
			resp = bytearray(resp)
			if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
				print("back button pressed")
				kill = 1  # BACK
				checkback = 1
				gameid = "exit"
				os._exit(0)
		except:
			pass
		time.sleep(0.2)


# Wait for a game to start and get the game id!
if sys.argv[1] == "New":
	gt = threading.Thread(target=newGameThread, args=())
	gt.daemon = True
	gt.start()
	bb = threading.Thread(target=backTest, args=())
	bb.daemon = True
	bb.start()
	while not gameid and not kill:
		newest = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc)
		time.sleep(0.5)  # wait a little before accessing ongoing games (maybe the opponent haven't  bben found yet)?
		game_ids = [game['gameId'] for game in client.games.get_ongoing(30)]
		for g in game_ids:
			a_game = client.games.export(g)
			game_start = a_game['createdAt']
			# remove all the ongoing games that started earlier than 3 minutes ago
			if game_start < datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(minutes=300000):
				continue
			# remove all the wrong timecontrols (if there were any)
			if not a_game.get('clock'):
				print(f'1 {g}')
				continue
			if (a_game['clock']['initial'] != (int(gtime)*60)) or (a_game['clock']['increment'] != int(ginc)):
				print(f'2 {g}')
				continue
			# are there some changes breaking compatibility in berserk?
			if isinstance(game_start, int):
				game_start = datetime.datetime.utcfromtimestamp(game_start/1000)
			if game_start > newest:
				newest = game_start
				gameid = g

elif sys.argv[1] == "Ongoing":
	logging.info(f"selected game id {gameid}")
elif sys.argv[1] == "Challenge":
	logging.info(f"selected challenge id {challengeid}")
	gt = threading.Thread(target=newChallengeThread, args=())
	gt.daemon = True
	gt.start()
	bb = threading.Thread(target=backTest, args=())
	bb.daemon = True
	bb.start()

	while gameid == "" and kill == 0:
		logging.info('.')
		ongoing_games = client.games.get_ongoing(10)
		for game in ongoing_games:
			if game["gameId"] == challengeid:
				gameid = challengeid
				break
	logging.info(f"challenge accepted. Current challenge id {gameid}")

else:
	raise ValueError(f"Wrong argv[1] value: {sys.argv[1]}")
#gt = threading.Thread(target=ongoingGameThread, args=())
	#gt.daemon = True
	#gt.start()
	#bb = threading.Thread(target=backTest, args=())
	#bb.daemon = True
	#bb.start()


checkback = 1

if kill == 1:
	print("exiting")
	sys.exit()

playeriswhite = -1
whiteplayer = ""
blackplayer = ""
whiteclock = 0
blackclock = 0
whiteincrement = 0
blackincrement = 0
winner= ''
fenlog = "/home/pi/centaur/fen.log"
f = open(fenlog, "w")
f.write("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
f.close()
starttime = -1

# This thread keeps track of the move, etc, data coming back from lichess
# We need to start it before gamemanager because we want the actual player information
def stateThread():
	global remotemoves
	global status
	global playeriswhite
	global player
	global whiteplayer
	global blackplayer
	global whiteclock
	global blackclock
	global whiteincrement
	global blackincrement
	global resign
	global winner
	global cwinner
	global wtime
	global btime
	global whitetime
	global blacktime
	global whiterating
	global blackrating
	global message1
	global sound
	global wking
	global bking
	global kill
	status = ""
	while kill == 0 and status != "mate" and status != "draw" and status != "resign" and status != "aborted" and status != "outoftime" and status != "timeout":
		buttonPress = 0
		gamestate = client.board.stream_game_state(gameid)
		for state in gamestate:
			print(state)
			message1 = str(state)
			print("message1 = ", message1)

			if 'chatLine' in message1 or 'opponentGone' in message1:
				time.sleep(0.1)
				continue
			
			if message1.find('moves'):
				c = message1.find("wtime")
				messagehelp = message1[c:len(message1)]
				print("messagehelp = ", messagehelp)
				# At this point if the string contains date then the time is in date format
				# otherwise it's in number format.
				whitetimemin = 0
				whitetimesec = 0
				if "date" not in messagehelp:
					whitetimesec = messagehelp[8:messagehelp.find(",")]
					
					# this can be removed when all the special message cases have been dealt with
					if whitetimesec == "":
						whitetimesec = "0"

					whitetimesec = str(int(whitetimesec)//1000)
				else:
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					whitetimemin = messagehelp[1:c]
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					whitetimesec = messagehelp[1:c]
					if whitetimesec[:2] == "tz" or whitetimesec[1:3] == "st":
						whitetimesec = "0"
				
				# this can be removed when all the special message cases have been dealt with
				if whitetimemin == '':
					whitetimemin = 0

				whitetime = (int(str(whitetimemin)) * 60) + int(str(whitetimesec))
					
				c = message1.find("btime")
				messagehelp = message1[c:len(message1)]
				print("messagehelp = ", messagehelp)

				blacktimemin = 0
				blacktimesec = 0
				if "date" not in messagehelp:
					blacktimesec = messagehelp[8:messagehelp.find(",")]

					# this can be removed when all the special message cases have been dealt with
					if blacktimesec == "":
						blacktimesec = "0"
					blacktimesec = str(int(blacktimesec)//1000)
				else:
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					blacktimemin = messagehelp[1:c]
					messagehelp = messagehelp[c + 1:len(messagehelp)]
					c = messagehelp.find(", ")
					blacktimesec = messagehelp[1:c]
					if blacktimesec[:2] == "tz" or blacktimesec[1:3] == "st":
						blacktimesec = "0"

				# this can be removed when all the special message cases have been dealt with
				if blacktimemin == '':
					blacktimemin = 0

				blacktime = (int(blacktimemin) * 60) + int(blacktimesec)
				gamemanager.setClock(whitetime, blacktime)
			if ('state' in state.keys()):
				remotemoves = state.get('state').get('moves')
				status = state.get('state').get('status')
			else:
				if ('moves' in state.keys()):
					remotemoves = state.get('moves')
				if ('status' in state.keys()):
					status = state.get('status')
			if status == "mate":
				winner = str(state.get('winner'))
			remotemoves = str(remotemoves)
			status = str(status)
			if ('text' in state.keys()):
				message = state.get('text')
				if message == "Takeback sent":
					client.board.post_message(gameid, 'Sorry , this external board can\'t handle takeback', spectator=False)
				if message == "Black offers draw":
					client.board.decline_draw(gameid)
					epaper.writeText(13,"DRAW OFFERED    ")
					board.beep(board.SOUND_GENERAL)
				if message == "White offers draw":
					client.board.decline_draw(gameid)
					epaper.writeText(13, "DRAW OFFERED    ")
					board.beep(board.SOUND_GENERAL)
			if status == 'resign':
				board.beep(board.SOUND_WRONG_MOVE)
				board.beep(board.SOUND_WRONG_MOVE)
				epaper.writeText(11, 'Resign')
				cwinner = str(state.get('winner'))
				epaper.writeText(12, cwinner + ' wins')
				epaper.writeText(13, 'pls wait restart..')
				time.sleep(15)
				kill = 1
				sys.exit()
			if status == 'aborted':
				board.beep(board.SOUND_WRONG_MOVE)
				board.beep(board.SOUND_WRONG_MOVE)
				epaper.writeText(11, 'Game aborted')
				winner = 'No Winner'
				epaper.writeText(12, 'No winner')
				epaper.writeText(13, 'pls wait restart..')
				kill = 1
				sys.exit()
			if status == 'outoftime':
				board.beep(board.SOUND_WRONG_MOVE)
				board.beep(board.SOUND_WRONG_MOVE)
				epaper.writeText(11, 'Out of time')
				cwinner = str(state.get('winner'))
				epaper.writeText(12, cwinner + ' wins')
				epaper.writeText(13, 'pls wait restart..')
				time.sleep(15)
				kill = 1
				sys.exit()
			if status == 'timeout':
				board.beep(board.SOUND_WRONG_MOVE)
				board.beep(board.SOUND_WRONG_MOVE)
				epaper.writeText(11, 'Out of time')
				cwinner = str(state.get('winner'))
				epaper.writeText(12, cwinner + ' wins')
				epaper.writeText(13, 'pls wait restart..')
				time.sleep(15)
				kill = 1
				sys.exit()
			if status == 'draw':
				board.beep(board.SOUND_WRONG_MOVE)
				board.beep(board.SOUND_WRONG_MOVE)
				epaper.writeText(11, 'Draw')
				cwinner = str(state.get('winner'))
				epaper.writeText(12, cwinner + ' No Winner')
				epaper.writeText(13, 'pls wait restart..')
				time.sleep(15)
				kill = 1
				sys.exit()

			if (remotemoves == "None"):
				remotemoves = ""
			if ('black' in state.keys()):
				if ('name' in state.get('white') or 'name' in state.get('black')):
					print(str(state.get('white').get('name')) + " vs " + str(state.get('black').get('name')))
					whiteplayer = str(state.get('white').get('name'))
					whiterating = str(state.get('white').get('rating'))
					blackplayer = str(state.get('black').get('name'))
					blackrating = str(state.get('black').get('rating'))
					if (str(state.get('white').get('name')) == player):
						playeriswhite = 1
					else:
						playeriswhite = 0
			if playeriswhite == 1:
				epaper.screeninverted = 0
			else:
				epaper.screeninverted = 1
			time.sleep(0.2)

st = threading.Thread(target=stateThread, args=())
st.daemon = True
st.start()

# Wait until we have the player details
while (whiteplayer == "" or blackplayer == "") and kill == 0:
	time.sleep(0.1)

if kill == 1:
	sys.exit()

wpl = whiteplayer + "(" + whiterating + ")"
bpl = blackplayer + "(" + blackrating + ")"
if blackplayer == "None" or blackplayer == None:
	bpl = "Lichess Computer"
	blackplayer = "Lichess Computer"
if whiteplayer == "None" or whiteplayer == None:
	wpl = "Lichess Computer"
	whiteplayer = "Lichess Computer"

gamemanager.setGameInfo("","","",wpl,bpl)

gamemanager.setClock(600,600)
gamemanager.startClock()

if kill == 0:
	# Subscribe to the game manager to activate the previous functions
	gamemanager.subscribeGame(eventCallback, moveCallback, keyCallback)
	epaper.writeText(0,"Place pieces in")
	epaper.writeText(1,"Starting Pos")




while kill == 0:
	time.sleep(0.1)
