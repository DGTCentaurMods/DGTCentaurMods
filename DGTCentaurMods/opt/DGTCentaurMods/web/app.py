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

from flask import Flask, render_template
from flask_socketio import SocketIO
from DGTCentaurMods.game.lib import common
from DGTCentaurMods.game.consts import consts

import logging


def tail(f, lines=1, _buffer=4098):
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # we found enough lines, get out
        # Removed this line because it was redundant the while will catch
        # it, I left it for history
        # if len(lines_found) > lines:
        #    break

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]


logging.getLogger('chess.engine').setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").propagate = False

WEB_NAME = "DGTCentaurMods web 2.0"

appFlask = Flask(__name__)

socketio = SocketIO(appFlask, cors_allowed_origins="*")

if __name__ == '__main__':
	print("Starting socketio server...")
	socketio.run(appFlask, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True)

@socketio.on('connect')
def on_connect():
    print("New client connected!")

	# We send back the stored FEN
    socketio.emit('message', {'fen': common.get_Centaur_FEN()})

	# We ask the app to send the current PGN and FEN to all connected clients
	# DONE FROM THE CLIENT
    # socketio.emit('request', {'fen':True, 'pgn': True})
    
@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected!')

@socketio.on('message')
def on_message(message):

    # Broadcast to all connected clients
    socketio.emit('message', message)
    
@socketio.on('request')
def on_request(message):
    
	# System request
	if "sys_action" in message:
		action = message["sys_action"]

		if action == "shutdown":
			os.system("pkill centaur")
			time.sleep(.5)
			os.system("sudo poweroff")

		if action == "reboot":
			os.system("pkill centaur")
			time.sleep(.5)
			os.system("sudo shutdown -r")

		if action == "restart_service":
			os.system("pkill centaur")
			time.sleep(.5)
			os.system("sudo systemctl restart DGTCentaurMods.service")

		if action == "log_events":
			message = {"log_data":tail(open(consts.LOG_FILENAME, "r"), 100)}
			socketio.emit('message', message)

	else:

		# Broadcast to all connected clients
		socketio.emit('request', message)

@appFlask.route("/")
def index():
	return render_template('2.0/index.html', data={"title":WEB_NAME, "boardsize": 550, "iconsize": int(550/9)})


# LEGACY WEB SITE - reachable thru http://localhost/legacy

from flask import Flask, render_template, Response, request, redirect
from DGTCentaurMods.db import models
import centaurflask
from PIL import Image, ImageDraw
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import select
from sqlalchemy import delete
import os
import time
import pathlib
import io
import chess
import chess.pgn
import json

appFlask.config['UCI_UPLOAD_EXTENSIONS'] = ['.txt']
appFlask.config['UCI_UPLOAD_PATH'] = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
@appFlask.route("/legacy")
def legacy():
	fenlog = "/home/pi/centaur/fen.log"
	if os.path.isfile(fenlog) == True:
		with open(fenlog, "r") as f:
			line = f.readline().split(" ")
			fen = line[0]
	else:
		fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
	return render_template('index.html', fen=fen)

@appFlask.route("/fen")
def fen():
	fenlog = "/home/pi/centaur/fen.log"
	if os.path.isfile(fenlog) == True:
		with open(fenlog, "r") as f:
			line = f.readline().split(" ")
			fen = line[0]
	else:
		fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
	return fen

@appFlask.route("/rodentivtuner")
def tuner():

        return render_template('rodentivtuner.html')

@appFlask.route("/rodentivtuner" , methods=["POST"])
def tuner_upload_file():
	uploaded_file = request.files['file']
	if uploaded_file.filename != '':
		file_ext = os.path.splitext(uploaded_file.filename)[1]
		file_name = os.path.splitext(uploaded_file.filename)[0]
		if file_ext not in appFlask.config['UCI_UPLOAD_EXTENSIONS']:
			abort(400)
		uploaded_file.save(os.path.join(appFlask.config['UCI_UPLOAD_PATH'] + "personalities/",uploaded_file.filename))
		with open(appFlask.config['UCI_UPLOAD_PATH'] + "personalities/basic.ini", "r+") as file:
			for line in file:
				if file_name in line:
					break
			else: # not found, we are at the eof
				file.write(file_name + '=' + file_name + '.txt\n') # append missing data
		with open(appFlask.config['UCI_UPLOAD_PATH'] + "rodentIV.uci", "r+") as file:
			for line in file:
				if file_name in line:
					break
			else: # not found, we are at the eof  
				file.write('\n') # append missing data
				file.write('[' + file_name + ']\n') # append missing data
				file.write('PersonalityFile = ' + file_name + ' ' + file_name + '.txt' + '\n') # append missing data
				file.write('UCI_LimitStrength = true\n') # append missing data
				file.write('UCI_Elo = 1200\n') # append missing data
	return render_template('index.html')
@appFlask.route("/pgn")
def pgn():
	return render_template('pgn.html')

@appFlask.route("/configure")
def configure():
	# Get the lichessapikey		
	return render_template('configure.html', lichesskey=centaurflask.get_lichess_api(), lichessrange=centaurflask.get_lichess_range())

@appFlask.route("/support")
def support():
	return render_template('support.html')

@appFlask.route("/license")
def license():
	return render_template('license.html')

@appFlask.route("/return2dgtcentaurmods")
def return2dgtcentaurmods():
	os.system("pkill centaur")
	time.sleep(1)
	os.system("sudo systemctl restart DGTCentaurMods.service")
	return "ok"

@appFlask.route("/shutdownboard")
def shutdownboard():
	os.system("pkill centaur")
	os.system("sudo poweroff")
	return "ok"

@appFlask.route("/lichesskey/<key>")
def lichesskey(key):
    centaurflask.set_lichess_api(key)
    os.system("sudo systemctl restart DGTCentaurMods.service")
    return "ok"

@appFlask.route("/lichessrange/<newrange>")
def lichessrange(newrange):
	centaurflask.set_lichess_range(newrange)
	return "ok"

@appFlask.route("/analyse/<gameid>")
def analyse(gameid):
	return render_template('analysis.html', gameid=gameid)

@appFlask.route("/deletegame/<gameid>")
def deletegame(gameid):
	Session = sessionmaker(bind=models.engine)
	session = Session()
	stmt = delete(models.GameMove).where(models.GameMove.gameid == gameid)
	session.execute(stmt)
	stmt = delete(models.Game).where(models.Game.id == gameid)
	session.execute(stmt)
	session.commit()
	session.close()
	return "ok"

@appFlask.route("/getgames/<page>")
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
		for x in range(0,10):
			gameitem = {}
			gameitem["id"] = str(gamedata[x+t][8])
			gameitem["created_at"] = str(gamedata[x+t][0])
			src = os.path.basename(str(gamedata[x + t][1]))
			if src.endswith('.py'):
				src = src[:-3]
			gameitem["source"] = src
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

@appFlask.route("/engines")
def engines():
	# Return a list of engines and uci files. Essentially the contents our our engines folder
	files = {}
	enginepath = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
	enginefiles = os.listdir(enginepath)
	x = 0
	for f in enginefiles:
		fn = str(f)
		files[x] = fn
		x = x + 1
	return json.dumps(files)

@appFlask.route("/uploadengine", methods=['POST'])
def uploadengine():
	if request.method != 'POST':
		return
	file = request.files['file']
	if file.filename == '':
		return
	file.save(os.path.join(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/",file.filename))
	os.chmod(os.path.join(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/",file.filename),0o777)
	return redirect("/configure")

@appFlask.route("/delengine/<enginename>")
def delengine(enginename):
	os.remove(os.path.join(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/", enginename))
	return "ok"

@appFlask.route("/getpgn/<gameid>")
def makePGN(gameid):
	# Export a PGN of the specified game
	Session = sessionmaker(bind=models.engine)
	session = Session()
	g= chess.pgn.Game()
	gamedata = session.execute(
		select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round, models.Game.white, models.Game.black, models.Game.result).
			where(models.Game.id == gameid)
	).first()
	src = os.path.basename(str(gamedata[1]))
	if src.endswith('.py'):
		src = src[:-3]
	g.headers["Source"] = src
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
moddate = -1
sc = None
if os.path.isfile(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg"):
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

@appFlask.route('/video')
def video_feed():
	return Response(generateVideoFrame(),mimetype='multipart/x-mixed-replace; boundary=frame')

