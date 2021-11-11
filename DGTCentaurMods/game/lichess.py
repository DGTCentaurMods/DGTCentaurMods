# Play a game on lichess
#
# This is the second version of this script, it uses gamemanager to ensure that the system
# gets all the benefits + any future upgrades.
#
# TODO
#
# Rating range in web interface
# Test Live Games
#
from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper
from DGTCentaurMods.board import centaur
from DGTCentaurMods.board import board

import time
import chess
import chess.engine
import sys
import pathlib
from random import randint
import berserk
import ssl
import threading
import os

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
			ret = client.board.make_move(gameid, move)
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
	epaper.writeText(0,"Error:        ")
	epaper.writeText(1,"lichess.py    ")
	epaper.writeText(2,"no parameter")
	epaper.writeText(3,"given!")
	time.sleep(10)
	kill = 1
	sys.exit()

if (len(sys.argv) > 1) and kill == 0:
	if (str(sys.argv[1]) != "current" and str(sys.argv[1]) != "New"):
		sys.exit()

gtime = 0
ginc = 0
grated = 0
gcolor = 0
if (len(sys.argv) > 1):
	if str(sys.argv[1]) == "New":
		gtime = str(sys.argv[2])
		ginc = str(sys.argv[3])
		grated = str(sys.argv[4])
		gcolor = str(sys.argv[5])

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
	if (gtime == '10' and ginc == '5' and grated == "False" and gcolor == "white"):
		client.board.seek(10, 5, rated=False, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '10' and ginc == '5' and grated == "False" and gcolor == "black"):
		client.board.seek(10, 5, rated=False, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '10' and ginc == '5' and grated == "False" and gcolor == "random"):
		client.board.seek(10, 5, rated=False, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '10' and ginc == '5' and grated == "True" and gcolor == "white"):
		client.board.seek(10, 5, rated=True, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '10' and ginc == '5' and grated == "True" and gcolor == "black"):
		client.board.seek(10, 5, rated=True, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '10' and ginc == '5' and grated == "True" and gcolor == "random"):
		client.board.seek(10, 5, rated=True, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '15' and ginc == '10' and grated == "False" and gcolor == "white"):
		client.board.seek(15, 10, rated=False, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '15' and ginc == '10' and grated == "False" and gcolor == "black"):
		client.board.seek(15, 10, rated=False, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '15' and ginc == '10' and grated == "False" and gcolor == "random"):
		client.board.seek(15, 10, rated=False, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '15' and ginc == '10' and grated == "True" and gcolor == "white"):
		client.board.seek(15, 10, rated=True, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '15' and ginc == '10' and grated == "True" and gcolor == "black"):
		client.board.seek(15, 10, rated=True, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '15' and ginc == '10' and grated == "True" and gcolor == "random"):
		client.board.seek(15, 10, rated=True, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '0' and grated == "False" and gcolor == "white"):
		client.board.seek(30, 0, rated=False, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '0' and grated == "False" and gcolor == "black"):
		client.board.seek(30, 0, rated=False, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '0' and grated == "False" and gcolor == "random"):
		client.board.seek(30, 0, rated=False, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '0' and grated == "True" and gcolor == "white"):
		client.board.seek(30, 0, rated=True, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '0' and grated == "True" and gcolor == "black"):
		client.board.seek(30, 0, rated=True, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '0' and grated == "True" and gcolor == "random"):
		client.board.seek(30, 0, rated=True, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '20' and grated == "False" and gcolor == "white"):
		client.board.seek(30, 20, rated=False, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '20' and grated == "False" and gcolor == "black"):
		client.board.seek(30, 20, rated=False, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '20' and grated == "False" and gcolor == "random"):
		client.board.seek(30, 20, rated=False, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '20' and grated == "True" and gcolor == "white"):
		client.board.seek(30, 20, rated=True, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '20' and grated == "True" and gcolor == "black"):
		client.board.seek(30, 20, rated=True, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '30' and ginc == '20' and grated == "True" and gcolor == "random"):
		client.board.seek(30, 20, rated=True, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '60' and ginc == '20' and grated == "False" and gcolor == "white"):
		client.board.seek(60, 20, rated=False, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '60' and ginc == '20' and grated == "False" and gcolor == "black"):
		client.board.seek(60, 20, rated=False, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '60' and ginc == '20' and grated == "False" and gcolor == "random"):
		client.board.seek(60, 20, rated=False, variant='standard', color='random', rating_range=f'{ratingrange}')
	if (gtime == '60' and ginc == '20' and grated == "True" and gcolor == "white"):
		client.board.seek(60, 20, rated=True, variant='standard', color='white', rating_range=f'{ratingrange}')
	if (gtime == '60' and ginc == '20' and grated == "True" and gcolor == "black"):
		client.board.seek(60, 20, rated=True, variant='standard', color='black', rating_range=f'{ratingrange}')
	if (gtime == '60' and ginc == '20' and grated == "True" and gcolor == "random"):
		client.board.seek(60, 20, rated=True, variant='standard', color='random', rating_range=f'{ratingrange}')

checkback = 0
kill = 0
gameid = ""

def backTest():
	# Check for the back button. We use this to allow the user to stop seeking for a game
	global kill
	global checkback
	global gameid
	while checkback == 0:
		try:
			tosend = bytearray(b'\x94\x06\x50\x6a')
			board.ser.write(tosend)
			resp = board.ser.read(10000)
			resp = bytearray(resp)
			if (resp.hex() == "b10011065000140a0501000000007d4700"):
				print("back button pressed")
				kill = 1  # BACK
				checkback = 1
				gameid = "exit"
				os._exit(0)
		except:
			pass
		time.sleep(0.2)

# Wait for a game to start and get the game id!
if (str(sys.argv[1]) == "New"):
	gt = threading.Thread(target=newGameThread, args=())
	gt.daemon = True
	gt.start()
	bb = threading.Thread(target=backTest, args=())
	bb.daemon = True
	bb.start()

while gameid == "" and kill == 0:
	for event in client.board.stream_incoming_events():
		if ('type' in event.keys()):
			if (event.get('type') == "gameStart"):
				if ('game' in event.keys()):
					gameid = event.get('game').get('id')
					break
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
			# print(message1)
			if message1.find('moves'):
				c = message1.find("wtime")
				messagehelp = message1[c:len(message1)]
				# At this point if the string contains date then the time is in date format
				# otherwise it's in number format.
				whitetimemin = 0
				whitetimesec = 0
				if "date" not in messagehelp:
					whitetimesec = messagehelp[8:messagehelp.find(",")]
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
				whitetime = (int(str(whitetimemin)) * 60) + int(str(whitetimesec))
				c = message1.find("btime")
				messagehelp = message1[c:len(message1)]
				blacktimemin = 0
				blacktimesec = 0
				if "date" not in messagehelp:
					blacktimesec = messagehelp[8:messagehelp.find(",")]
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
