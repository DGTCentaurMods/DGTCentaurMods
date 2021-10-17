from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper

import time

def keyCallback(key):
	# This function will receive any keys presses on the keys
	# under the display. Possibles:
	# gamemanager.BTNBACK  gamemanager.BTNTICK  gamemanager.BTNUP
	# gamemanager.BTNDOWN  gamemanager.BTNHELP  gamemanager.BTNPLAY
	print("Key event received: " + str(key))

def eventCallback(event):
	# This function receives event callbacks about the game in play
	if event == gamemanager.EVENT_NEW_GAME:
		epaper.writeText(0,"New Game")
		epaper.drawFen(gamemanager.board.fen())
	if event == gamemanager.EVENT_WHITE_TURN:
		epaper.writeText(0,"White turn")
	if event == gamemanager.EVENT_BLACK_TURN:
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
			epaper.writeText(1,event[12:])

def moveCallback(move):
	# This function receives valid moves made on the board
	# Note: the board state is in python-chess object gamemanager.board
	epaper.drawFen(gamemanager.board.fen())
	epaper.writeText(9, move)


# Activate the epaper
epaper.initEpaper()

# Subscribe to the game manager to activate the previous functions
gamemanager.subscribeGame(eventCallback, moveCallback, keyCallback)
epaper.drawFen(gamemanager.board.fen())

while True:
	time.sleep(0.1)
