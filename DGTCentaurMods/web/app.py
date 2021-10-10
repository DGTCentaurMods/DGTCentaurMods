from flask import Flask, render_template
from board import LiveBoard

app = Flask(__name__)

@app.route("/")
def index():
	fen = "rnbqkbnr/pppp1ppp/4p3/8/3P4/8/PPP1PPPP/RNBQKBNR"
	return render_template('index.html', fen=fen)


