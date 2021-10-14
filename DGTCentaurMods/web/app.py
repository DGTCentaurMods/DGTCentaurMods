from flask import Flask, render_template
from board import LiveBoard

app = Flask(__name__)

@app.route("/")
def index():
    fenlog = "/home/pi/centaur/fen.log"
    with open(fenlog, "r") as f:
        line = f.readline().split(' ')
        fen = line[0]
    return render_template('index.html', fen=fen)


