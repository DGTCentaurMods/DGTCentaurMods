# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
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
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from flask import Flask, render_template
from flask_socketio import SocketIO

from DGTCentaurMods.game.lib import common
from DGTCentaurMods.game.consts import consts
from DGTCentaurMods.game.classes import DAL

import os, time, logging

#logging.getLogger('chess.engine').setLevel(logging.CRITICAL)
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

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected!')

@socketio.on('message')
def on_message(message):

    # Broadcast to all connected clients
    socketio.emit('message', message)
    
@socketio.on('request')
def on_request(message):

	response = {}
	
	# We send back the UUID if the request contains one
	if "uuid" in message:
		response["uuid"] = message["uuid"]

	# System request
	if "sys" in message:
		action = message["sys"]

		if action == "shutdown":
			# We relay the message to the app
			socketio.emit('request', message)
			os.system("pkill centaur")
			time.sleep(.5)
			os.system("sudo poweroff")

		if action == "reboot":
			# We relay the message to the app
			socketio.emit('request', message)
			os.system("pkill centaur")
			time.sleep(.5)
			os.system("sudo reboot")

		if action == "restart_service":
			os.system("pkill centaur")
			time.sleep(.5)
			os.system("sudo systemctl restart DGTCentaurMods.service")

		if action == "log_events":
			response["log_events"] = common.tail(open(consts.LOG_FILENAME, "r"), 100)
			socketio.emit('message', response)

	else:

		if "data" in message:
			action = message["data"]

			_dal = DAL.get()

			if action == "previous_games":
				response["previous_games"] = _dal.get_all_games()
				socketio.emit('message', response)

			if action == "game_moves":
				response["game_moves"] = _dal.read_game_moves_by_id(message["id"])
				socketio.emit('message', response)

			if action == "remove_game":

				print(f'Request from client:{action}({message["id"]})')

				if _dal.remove_game_by_id(message["id"]):
					response["popup"] = "The game has been successfuly removed!"
				else:
					response["popup"] = "An error occured during the delete process!"

				socketio.emit('message', response)

		else:

			# Broadcast to all connected clients
			socketio.emit('request', message)

@appFlask.route("/")
def index():
	return render_template('2.0/index.html', data={"title":consts.WEB_NAME, "boardsize": 550, "iconsize": int(550/9)})
