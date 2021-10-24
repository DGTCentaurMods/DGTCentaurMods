from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper

import time

global curturn

def keyCallback(key):
	# This function will receive any keys presses on the keys
	# under the display. Possibles:
	# gamemanager.BTNBACK  gamemanager.BTNTICK  gamemanager.BTNUP
	# gamemanager.BTNDOWN  gamemanager.BTNHELP  gamemanager.BTNPLAY
	print("Key event received: " + str(key))

def eventCallback(event):
	global curturn
	# This function receives event callbacks about the game in play
	if event == gamemanager.EVENT_NEW_GAME:
		epaper.writeText(0,"New Game")
		curturn = 1
		epaper.drawFen(gamemanager.cboard.fen())
	if event == gamemanager.EVENT_WHITE_TURN:
		curturn = 1
		epaper.writeText(0,"White turn")
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		epaper.writeText(0,"Black turn")
		# Here you would calculate and set the move the computer wants to make.
		# But for an example  just set a specific move you'd do
		# gamemanager.computerMove("b7b5")

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

def moveCallback(move):
	# This function receives valid moves made on the board
	# Note: the board state is in python-chess object gamemanager.cboard
	epaper.drawFen(gamemanager.cboard.fen())
	epaper.writeText(9, move)


# Activate the epaper
epaper.initEpaper()

# Set the initial state of curturn to indicate white's turn
curturn = 1

# Subscribe to the game manager to activate the previous functions
gamemanager.subscribeGame(eventCallback, moveCallback, keyCallback)
epaper.drawFen(gamemanager.cboard.fen())

while True:
	time.sleep(0.1)
