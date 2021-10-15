from flask import Flask, render_template, Response
from board import LiveBoard
from PIL import Image, ImageDraw, ImageFont
import os
import pathlib
import io

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
def generateVideoFrame():
	global pb, pw
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
		sc = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg")
		image.paste(sc, (345 + 1216 - 130, 635))
		logo = Image.open(str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/logo_mods_web.png")
		image.paste(logo, (345 + 1216 - 130, 0), logo)
		output = io.BytesIO()
		image = image.convert("RGB")
		image.save(output, "JPEG")
		yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + output.getvalue() + b'\r\n')

@app.route('/video')
def video_feed():
	return Response(generateVideoFrame(),mimetype='multipart/x-mixed-replace; boundary=frame')
