from flask import Flask, render_template
from board import LiveBoard
import os

app = Flask(__name__)

@app.route("/")
def index():
	fenlog = "/home/pi/centaur/fen.log"
	if os.path.isfile(fenlog) == True:
		with open(fenlog, "r") as f:
			line = f.readline().split(" ")
			fen = line[0]
	else:
		fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
	return render_template('index.html', fen=fen)

@app.route("/fen")
def fen():
	fenlog = "/home/pi/centaur/fen.log"
	if os.path.isfile(fenlog) == True:
		with open(fenlog, "r") as f:
			line = f.readline().split(" ")
			fen = line[0]
	else:
		fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
	return fen