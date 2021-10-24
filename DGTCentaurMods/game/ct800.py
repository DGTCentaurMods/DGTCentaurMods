# Play pure ct800 without DGT Centaur Adaptive Play
#
from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper

import time
import chess
import chess.engine
import sys
import pathlib
from random import randint

curturn = 1
computeronturn = 0
kill = 0

# Expect the first argument to be 'white' 'black' or 'random' for what the player is playing
computerarg = sys.argv[1]
if computerarg == "white":
	computeronturn = 0
if computerarg == "black":
	computeronturn = 1
if computerarg == "random":
	computeronturn = randint(0,1)

# Pass an ELO between 1000 and 2400
eloarg = int(sys.argv[2])

if computeronturn == 0:
	gamemanager.setGameInfo(str(eloarg) + " ELO", "", "", "Player", "CT800")
else:
	gamemanager.setGameInfo(str(eloarg) + " ELO", "", "", "CT800", "Player")

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
	# This function receives event callbacks about the game in play
	if event == gamemanager.EVENT_NEW_GAME:
		epaper.writeText(0,"New Game")
		epaper.writeText(1,"               ")
		curturn = 1
		epaper.drawFen(gamemanager.cboard.fen())
	if event == gamemanager.EVENT_WHITE_TURN:
		curturn = 1
		epaper.writeText(0,"White turn")
		if curturn == computeronturn:
			engine = chess.engine.SimpleEngine.popen_uci(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/ct800")
			options = ({"UCI_LimitStrength": True, "UCI_Elo": eloarg})
			engine.configure(options)
			limit = chess.engine.Limit(time=5)
			mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
			mv = mv.move
			epaper.writeText(12, "Engine: " + str(mv))
			engine.quit()
			gamemanager.computerMove(str(mv))
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		epaper.writeText(0,"Black turn")
		if curturn == computeronturn:
			engine = chess.engine.SimpleEngine.popen_uci(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/ct800")
			options = ({"UCI_LimitStrength": True, "UCI_Elo": eloarg})
			engine.configure(options)
			limit = chess.engine.Limit(time=5)
			mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
			mv = mv.move
			epaper.writeText(12,"Engine: " + str(mv))
			engine.quit()
			gamemanager.computerMove(str(mv))

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
			epaper.writeText(1,event[12:])
			time.sleep(10)
			kill = 1

def moveCallback(move):
	# This function receives valid moves made on the board
	# Note: the board state is in python-chess object gamemanager.cboard
	epaper.drawFen(gamemanager.cboard.fen())
	epaper.writeText(9, move)


# Activate the epaper
epaper.initEpaper()

# Set the initial state of curturn to indicate white's turn
curturn = 1
if computeronturn == 0:
	epaper.writeText(9,"You are WHITE")
else:
	epaper.writeText(9,"You are BLACK")

# Subscribe to the game manager to activate the previous functions
gamemanager.subscribeGame(eventCallback, moveCallback, keyCallback)
epaper.writeText(0,"Place pieces in")
epaper.writeText(1,"Starting Pos")


while kill == 0:
	time.sleep(0.1)
