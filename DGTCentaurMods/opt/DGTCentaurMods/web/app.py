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
from DGTCentaurMods.game.classes import DAL

import os, time, logging


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
			response = {"log_data":tail(open(consts.LOG_FILENAME, "r"), 100)}

			if "uuid" in message:
				response["uuid"] = message["uuid"]

			socketio.emit('message', response)

	else:

		if "data" in message:
			action = message["data"]

			_dal = DAL.get()

			if action == "previous_games":
				response = {"previous_games": _dal.get_all_games()}
				socketio.emit('message', response)

			if action == "game_moves":
				response = {"game_moves": _dal.read_game_moves_by_id(message["id"])}
				socketio.emit('message', response)

			if action == "remove_game":

				print(f'Request from client:{action}({message["id"]})')

				if _dal.remove_game_by_id(message["id"]):
					socketio.emit('message',  {"popup":"The game has been successfuly removed!"})
				else:
					socketio.emit('message', {"popup":"An error occured during the delete process!"})

		else:

			# Broadcast to all connected clients
			socketio.emit('request', message)

@appFlask.route("/")
def index():
	return render_template('2.0/index.html', data={"title":consts.WEB_NAME, "boardsize": 550, "iconsize": int(550/9)})
