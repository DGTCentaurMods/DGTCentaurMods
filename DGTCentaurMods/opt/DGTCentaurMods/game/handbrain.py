# Play hand and brain chess with the selected engine
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
from DGTCentaurMods.board import *

import time
import chess
import chess.engine
import sys
import pathlib
from random import randint
import configparser

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

# Arg2 is going to contain the name of our engine choice. We use this for database logging and to spawn the engine
enginename = sys.argv[2]

ucioptionsdesc = "Default"
ucioptions = {}
if len(sys.argv) > 3:
	# This also has an options string...but what is actually passed in 3 is the desc which is the section name
	ucioptionsdesc = sys.argv[3]
	# These options we should derive form the uci file
	ucifile = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/" + enginename + ".uci"
	config = configparser.ConfigParser()
	config.optionxform = str
	config.read(ucifile)
	print(config.items(ucioptionsdesc))
	for item in config.items(ucioptionsdesc):
		ucioptions[item[0]] = item[1]
	print(ucioptions)

if computeronturn == 0:
	gamemanager.setGameInfo(ucioptionsdesc, "", "", "Player", enginename)
else:
	gamemanager.setGameInfo(ucioptionsdesc, "", "", enginename, "Player")

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
			engine = chess.engine.SimpleEngine.popen_uci(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/" + enginename)
			if ucioptions != {}:
				options = (ucioptions)
				engine.configure(options)
			limit = chess.engine.Limit(time=5)
			mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
			mv = mv.move
			epaper.writeText(12, "Engine: " + str(mv))
			engine.quit()
			gamemanager.computerMove(str(mv))
		else:
			proc = 1
			if type(event) == str:
				if event.startswith("Termination."):
					proc = 0
			# It is not the computer's turn. But get a suggestion from stockfish
			if proc == 1:
				engine = chess.engine.SimpleEngine.popen_uci("/home/pi/centaur/engines/stockfish_pi")
				limit = chess.engine.Limit(time=5)
				mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
				mv = mv.move
				mv = str(mv)[:2]
				sqnum = chess.parse_square(str(mv))
				piecesq = gamemanager.cboard.piece_at(sqnum)
				sqs = []
				for i in range(0,64):
					if gamemanager.cboard.piece_at(i) == piecesq:
						sqs.append(i)
				board.ledArray(sqs,20)
				epaper.writeText(13, "BRAIN SAYS: " + str(piecesq))
				engine.quit();
	if event == gamemanager.EVENT_BLACK_TURN:
		curturn = 0
		epaper.writeText(0,"Black turn")
		if curturn == computeronturn:
			engine = chess.engine.SimpleEngine.popen_uci(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/" + enginename)
			if ucioptions != {}:
				options = (ucioptions)
				engine.configure(options)
			limit = chess.engine.Limit(time=5)
			mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
			mv = mv.move
			epaper.writeText(12,"Engine: " + str(mv))
			engine.quit()
			gamemanager.computerMove(str(mv))
		else:
			proc = 1
			if type(event) == str:
				if event.startswith("Termination."):
					proc = 0
			# It is not the computer's turn. But get a suggestion from stockfish
			if proc == 1:
				engine = chess.engine.SimpleEngine.popen_uci("/home/pi/centaur/engines/stockfish_pi")
				limit = chess.engine.Limit(time=5)
				mv = engine.play(gamemanager.cboard, limit, info=chess.engine.INFO_ALL)
				mv = mv.move
				mv = str(mv)[:2]
				sqnum = chess.parse_square(str(mv))
				piecesq = gamemanager.cboard.piece_at(sqnum)
				sqs = []
				for i in range(0,64):
					if gamemanager.cboard.piece_at(i) == piecesq:
						sqs.append(i)
				board.ledArray(sqs,20)
				epaper.writeText(13, "BRAIN SAYS: " + str(piecesq))
				engine.quit();
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
