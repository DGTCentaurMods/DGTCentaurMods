from flask import Flask, render_template, Response
from DGTCentaurMods.db import models
from DGTCentaurMods.board import centaur
from board import LiveBoard
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import func
from sqlalchemy import select
import os
import pathlib
import io
import chess
import chess.pgn
import json

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

@app.route("/pgn")
def pgn():
	return render_template('pgn.html')

@app.route("/configure")
def configure():
	# Get the lichessapikey
	return render_template('configure.html', lichesskey=centaur.get_lichess_api())

@app.route("/lichesskey/<key>")
def lichesskey(key):
	centaur.set_lichess_api(key)
	return "ok"

@app.route("/analyse/<gameid>")
def analyse(gameid):
	return render_template('analysis.html', gameid=gameid)

@app.route("/getgames/<page>")
def getGames(page):
	# Return batches of 10 games by listing games in reverse order
	Session = sessionmaker(bind=models.engine)
	session = Session()
	gamedata = session.execute(
		select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round,
			   models.Game.white, models.Game.black, models.Game.result, models.Game.id).
			order_by(models.Game.id.desc())
	).all()
	t = (int(page) * 10) - 10
	games = {}
	try:
		for x in range(0,20):
			gameitem = {}
			gameitem["id"] = str(gamedata[x+t][8])
			gameitem["created_at"] = str(gamedata[x+t][0])
			gameitem["source"] = os.path.basename(str(gamedata[x + t][1]))
			gameitem["event"] = str(gamedata[x + t][2])
			gameitem["site"] = str(gamedata[x + t][3])
			gameitem["round"] = str(gamedata[x + t][4])
			gameitem["white"] = str(gamedata[x + t][5])
			gameitem["black"] = str(gamedata[x + t][6])
			gameitem["result"] = str(gamedata[x + t][7])
			games[x] = gameitem
	except:
		pass
	session.close()
	return json.dumps(games)

@app.route("/getpgn/<gameid>")
def makePGN(gameid):
	# Export a PGN of the specified game
	Session = sessionmaker(bind=models.engine)
	session = Session()
	g= chess.pgn.Game()
	gamedata = session.execute(
		select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round, models.Game.white, models.Game.black, models.Game.result).
			where(models.Game.id == gameid)
	).first()
	g.headers["Source"] = os.path.basename(str(gamedata[1]))
	g.headers["Date"] = str(gamedata[0])
	g.headers["Event"] = str(gamedata[2])
	g.headers["Site"] = str(gamedata[3])
	g.headers["Round"] = str(gamedata[4])
	g.headers["White"] = str(gamedata[5])
	g.headers["Black"] = str(gamedata[6])
	g.headers["Result"] = str(gamedata[7])
	for key in g.headers:
			if g.headers[key] == "None":
				g.headers[key] = ""
	print(gamedata)
	moves = session.execute(
		select(models.GameMove.move_at, models.GameMove.move, models.GameMove.fen).
			where(models.GameMove.gameid == gameid)
	).all()
	first = 1
	node = None
	for x in range(0,len(moves)):
		if moves[x][1] != '':
			if first == 1:
				node = g.add_variation(chess.Move.from_uci(moves[x][1]))
				first = 0
			else:
				node = node.add_variation(chess.Move.from_uci(moves[x][1]))
	exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
	pgn_string = g.accept(exporter)
	session.close()
	return pgn_string

pb = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/pb.png").convert("RGBA")
pw = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/pw.png").convert("RGBA")
rb = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/rb.png").convert("RGBA")
bb = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/bb.png").convert("RGBA")
nb = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/nb.png").convert("RGBA")
qb = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/qb.png").convert("RGBA")
kb = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/kb.png").convert("RGBA")
rw = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/rw.png").convert("RGBA")
bw = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/bw.png").convert("RGBA")
nw = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/nw.png").convert("RGBA")
qw = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/qw.png").convert("RGBA")
kw = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/kw.png").convert("RGBA")
logo = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/logo_mods_web.png")
sc = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")
moddate = os.stat(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")[8]
def generateVideoFrame():
	global pb, pw, rb, bb, nb, qb, kb, rw, bw, nw, qw, kw, logo, sc, moddate
	while True:
		fenlog = "/home/pi/centaur/fen.log"
		f = open(fenlog, "r")
		curfen = f.readline()
		f.close()
		curfen = curfen.replace("/", "")
		curfen = curfen.replace("1", " ")
		curfen = curfen.replace("2", "  ")
		curfen = curfen.replace("3", "   ")
		curfen = curfen.replace("4", "    ")
		curfen = curfen.replace("5", "     ")
		curfen = curfen.replace("6", "      ")
		curfen = curfen.replace("7", "       ")
		curfen = curfen.replace("8", "        ")
		image = Image.new(mode="RGBA", size=(1920, 1080), color=(255, 255, 255))
		draw = ImageDraw.Draw(image)
		draw.rectangle([(345, 0), (345 + 1329 - 100, 1080)], fill=(33, 33, 33), outline=(33, 33, 33))
		draw.rectangle([(345 + 9, 9), (345 + 1220 - 149, 1071)], fill=(225, 225, 225), outline=(225, 225, 225))
		draw.rectangle([(345 + 12, 12), (345 + 1216 - 149, 1067)], fill=(33, 33, 33), outline=(33, 33, 33))
		col = 229
		xp = 345 + 16
		yp = 16
		sqsize = 130.9
		for r in range(0, 8):
			if r / 2 == r // 2:
				col = 229
			else:
				col = 178
			for c in range(0, 8):
				draw.rectangle([(xp, yp), (xp + sqsize, yp + sqsize)], fill=(col, col, col), outline=(col, col, col))
				xp = xp + sqsize
				if col == 178:
					col = 229
				else:
					col = 178
			yp = yp + sqsize
			xp = 345 + 16
		row = 0
		col = 0
		for r in range(0, 64):
			item = curfen[r]
			if item == "r":
				image.paste(rb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), rb)
			if item == "b":
				image.paste(bb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), bb)
			if item == "n":
				image.paste(nb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), nb)
			if item == "q":
				image.paste(qb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), qb)
			if item == "k":
				image.paste(kb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), kb)
			if item == "p":
				image.paste(pb, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), pb)
			if item == "R":
				image.paste(rw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), rw)
			if item == "B":
				image.paste(bw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), bw)
			if item == "N":
				image.paste(nw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), nw)
			if item == "Q":
				image.paste(qw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), qw)
			if item == "K":
				image.paste(kw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), kw)
			if item == "P":
				image.paste(pw, (345 + 18 + (int)(col * sqsize + 1), 16 + (int)(row * sqsize + 1)), pw)
			col = col + 1
			if col == 8:
				col = 0
				row = row + 1
		newmoddate = os.stat(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")[8]
		if newmoddate != moddate:
			sc = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")
			moddate = newmoddate
		image.paste(sc, (345 + 1216 - 130, 635))
		image.paste(logo, (345 + 1216 - 130, 0), logo)
		output = io.BytesIO()
		image = image.convert("RGB")
		image.save(output, "JPEG", quality=30)
		cnn = output.getvalue()
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n'
			b'Content-Length: ' + f"{len(cnn)}".encode() + b'\r\n'
			b'\r\n' + cnn + b'\r\n')

@app.route('/video')
def video_feed():
	return Response(generateVideoFrame(),mimetype='multipart/x-mixed-replace; boundary=frame')
