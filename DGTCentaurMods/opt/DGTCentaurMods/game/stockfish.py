# Play pure stockfish without DGT Centaur Adaptive Play
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

import time
import chess
import chess.engine
import sys
from random import randint

curturn = 1
engine = chess.engine.SimpleEngine.popen_uci("/home/pi/centaur/engines/stockfish_pi")
computeronturn = 0
kill = 0
# Pass an ELO between 1350 and 2850
eloarg = int(sys.argv[2])

# Expect the first argument to be 'white' 'black' or 'random' for what the player is playing
computerarg = sys.argv[1]
if computerarg == "white":
	computeronturn = 0
if computerarg == "black":
	computeronturn = 1
if computerarg == "random":
	computeronturn = randint(0,1)

if computeronturn == 0:
	gamemanager.setGameInfo(str(eloarg) + " ELO", "", "", "Player", "Stockfish UCI")
else:
	gamemanager.setGameInfo(str(eloarg) + " ELO", "", "", "Stockfish UCI", "Player")

def keyCallback(key):
	# This function will receive any keys presses on the keys
	# under the display. Possibles:
	# gamemanager.BTNBACK  gamemanager.BTNTICK  gamemanager.BTNUP
	# gamemanager.BTNDOWN  gamemanager.BTNHELP  gamemanager.BTNPLAY
	global kill
	global engine
	print("Key event received: " + str(key))
	if key == gamemanager.BTNBACK:
		print("kill hit")
		kill = 1
		engine.quit()

def eventCallback(event):
	global curturn
	global engine
	global eloarg
	global kill
	# This function receives event callbacks about the game in play
	if event == gamemanager.EVENT_NEW_GAME:
		epaper.writeText(0,"New Game")
		epaper.writeText(1, "               ")
		curturn = 1
		epaper.drawFen(gamemanager.cboard.fen())
	if event == gamemanager.EVENT_WHITE_TURN:
		curturn = 1
		epaper.writeText(0,"White turn")
		if curturn == computeronturn:
			options = ({"UCI_LimitStrength": True, "UCI_Elo": eloarg})
			engine.configure(options)
			limit = chess.engine.Limit(time=2)
			mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
			print(mv)
			mv = mv.move
			epaper.writeText(12, "Engine: " + str(mv))
			gamemanager.computerMove(str(mv))
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		epaper.writeText(0,"Black turn")
		if curturn == computeronturn:
			options = ({"UCI_LimitStrength": True, "UCI_Elo": eloarg})
			engine.configure(options)
			limit = chess.engine.Limit(time=2)
			mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_BASIC)
			print(mv)
			mv = mv.move
			epaper.writeText(12, "Engine: " + str(mv))
			gamemanager.computerMove(str(mv))
	if event == gamemanager.EVENT_RESIGN_GAME:
		gamemanager.resignGame(computeronturn + 1)

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
	# Note: the board state is in python-chess object gamemanager.board
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
