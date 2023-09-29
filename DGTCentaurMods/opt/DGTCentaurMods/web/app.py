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

from DGTCentaurMods.lib import common
from DGTCentaurMods.consts import consts, menu
from DGTCentaurMods.classes import DAL, SocketClient, Log
from DGTCentaurMods.classes.CentaurConfig import CentaurConfig

import os, time, logging, subprocess, uuid

SOCKET_EX = SocketClient.get()

#logging.getLogger('chess.engine').setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").propagate = False

# Centaur UUID
CUUID = CentaurConfig.get_system_settings("cuuid", uuid.uuid4())
CentaurConfig.update_system_settings("cuuid", CUUID)

appFlask = Flask(__name__)

socketio = SocketIO(appFlask, cors_allowed_origins="*")

Log.debug("-> Starting socketio server...", console=True)

if __name__ == '__main__':
	#socketio.run(appFlask, port=5000, host='0.0.0.0', ssl_context='adhoc', allow_unsafe_werkzeug=True)
	socketio.run(appFlask, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True)


def on_external_socket_request(message, socket):

	try:
		# The chat message comes from outside
		if "chat_message" in message:
			# External message
			# Broadcast to all connected local clients
			# We reject anonymous messages
			if not "cuuid" in message["chat_message"]:
				return

			socketio.emit('web_message', message)

		# The external request comes from outside
		if consts.EXTERNAL_REQUEST in message:
			# External message
			# Broadcast to all connected local clients
			# We reject anonymous messages
			if not "cuuid" in message[consts.EXTERNAL_REQUEST]:
				return
			
			# If we are the source, we reject the request
			if message[consts.EXTERNAL_REQUEST]["cuuid"] == CUUID:
				return

			socketio.emit('request', message)

	except Exception as e:
		Log.exception(on_external_socket_request.__name__, e)
		pass

@socketio.on('connect')
def on_connect():
	print("New client connected!")

	# We send back the stored FEN
	socketio.emit('web_message', {'fen': common.get_Centaur_FEN()})

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected!')

@socketio.on('web_message')
def on_web_message(message):

	try:
		if consts.EXTERNAL_REQUEST in message:
			message[consts.EXTERNAL_REQUEST]["cuuid"] = CUUID

			SOCKET_EX.send_request(message)

		# The chat message comes from inside
		elif "chat_message" in message:
			# Broadcast to all connected external clients
			# The message becomes a request to be handled by external clients

			message["chat_message"]["cuuid"] = CUUID

			SOCKET_EX.send_request(message)

		else:
			# Internal message
			# Broadcast to all connected local web clients
			socketio.emit('web_message', message)

	except Exception as e:
		Log.exception(on_web_message.__name__, e)
		pass

@socketio.on('request')
def on_request(message):

	if not SOCKET_EX.initialized:
		SOCKET_EX.initialize(uri=CentaurConfig.get_external_socket_server(),
					   on_socket_request=on_external_socket_request)

	# We send back the username and the CUUID to the local web clients
	response = {
		"username":CentaurConfig.get_lichess_settings("username") or "Anonymous",
		"cuuid":CUUID,
	}

	# We send back the UUID if the request contains one
	if "uuid" in message:
		response["uuid"] = message["uuid"]

	if "web_menu" in message:

		# Minimalist menu when the core service is down
		response["update_menu"] = menu.get_minimalist_menu()
		socketio.emit('web_message', response)
		del response["update_menu"]

	# Script request
	if "script" in message:
		script = message["script"]

		try:
			result = subprocess.check_output(["python3", f"{consts.OPT_DIRECTORY}/scripts/{script}.py"])

			response["script_output"] = result.decode()
			socketio.emit('web_message', response)
		
		except Exception as e:
			response["script_output"] = str(e)
			socketio.emit('web_message', response)
			
			pass

	# System request
	if "sys" in message:
		action = message["sys"]

		if action == "homescreen":
			# We relay the message to the app
			socketio.emit('request', message)

		if action == "centaur":
			# We relay the message to the app
			socketio.emit('request', message)
			time.sleep(4)

			os.system(f"sudo systemctl stop {consts.MAIN_ID}.service")

			time.sleep(.5)
			os.chdir(f"{consts.HOME_DIRECTORY}/centaur")
			os.system("sudo ./centaur")

		if action == "shutdown":
			# We relay the message to the app
			socketio.emit('request', message)
			time.sleep(4)

			os.system(f"sudo systemctl stop {consts.MAIN_ID}.service")
			time.sleep(.5)
			os.system("sudo init 0")

		if action == "restart_service":
			# We relay the message to the app
			socketio.emit('request', message)
			time.sleep(4)

			os.system("sudo pkill centaur")
			time.sleep(.5)
			os.system(f"sudo systemctl restart {consts.MAIN_ID}.service")

		if action == "restart_web_service":
			# We relay the message to the app
			socketio.emit('request', message)
			time.sleep(4)

			os.system("sudo pkill centaur")
			time.sleep(.5)
			os.system(f"sudo systemctl restart {consts.MAIN_ID}Web.service")

		if action == "log_events":
			response["log_events"] = common.tail(open(consts.LOG_FILENAME, "r"), 500)
			socketio.emit('web_message', response)

	else:

		_get_file_descriptor = lambda action:{
			"plugin":{
				"directory":consts.PLUGINS_DIRECTORY,
				"label":"plugin script",
				"extension":"py",
				"editable_name":True,
				"can_delete":False,
			},
			"uci":{
				"directory":consts.ENGINES_DIRECTORY,
				"label":"UCI File",
				"extension":"uci",
				"editable_name":False,
				"can_delete":False,
			},
			"famous_pgn":{
				"directory":consts.FAMOUS_DIRECTORY,
				"label":"famous PGN File",
				"extension":"pgn",
				"editable_name":True,
				"can_delete":True,
			},
			"conf":{
				"directory":f"{consts.OPT_DIRECTORY}/config",
				"label":"configuration file",
				"extension":"ini",
				"editable_name":False,
				"can_delete":False,
			},
		}[action['id']]


		if "read" in message:
			action = message["read"]

			try:
				file_descriptor = _get_file_descriptor(action)
			except:
				file_descriptor = None
				pass

			if file_descriptor:

				path = file_descriptor["directory"]+'/'+action["file"]+'.'+file_descriptor["extension"]

				if action["file"] == "__new__":
					contents = f'Your {file_descriptor["label"]} contents is there.'
				else:
					f = open(path, "r")
					contents = f.read()
					f.close()

				response["editor"] = {
					"id":action["id"],
					"text":contents,
					#"path":path,
					"file":action["file"],
					"new_file":action["file"],
					"extension":file_descriptor["extension"],
					"editable_name":file_descriptor["editable_name"],
					"can_delete":file_descriptor["can_delete"],
				}
				
				socketio.emit('web_message', response)
			return

		if "write" in message:

			action = message["write"]

			try:
				file_descriptor = _get_file_descriptor(action)
			except:
				pass

			if file_descriptor:

				path = file_descriptor["directory"]+'/'+action["file"]+'.'+file_descriptor["extension"]

				if action["new_file"] == "__new__":

					response["popup"] = "You need to rename your " + file_descriptor["label"] + "!"
					socketio.emit('web_message', response)

					return
				
				if action["new_file"] == "__delete__" and file_descriptor["can_delete"]:

					os.system(f'sudo rm -f "{path}"')

					response["popup"] = "The " + file_descriptor["label"] + " has been successfuly deleted!"
					socketio.emit('web_message', response)

					return

				f = open(path, "w")

				f.write(action["text"])
				f.close()

				if action["new_file"] != action["file"]:
					newpath = file_descriptor["directory"]+'/'+action["new_file"]+'.'+file_descriptor["extension"]
					os.system(f'sudo mv "{path}" "{newpath}"')

				response["popup"] = "The " + file_descriptor["label"] + " has been successfuly updated!"
				socketio.emit('web_message', response)
			return
		
		if "data" in message:
			action = message["data"]

			_dal = DAL.get()

			if action == "previous_games":
				response["previous_games"] = _dal.get_all_games()
				socketio.emit('web_message', response)

			if action == "sounds_settings_set":

				if "value" in message:
					CentaurConfig.update_sound_settings(message["value"]["id"], message["value"]["value"])

			if action == "sounds_settings":
				
				# We read the sounds settings
				for s in consts.SOUNDS_SETTINGS:
					s["value"] = CentaurConfig.get_sound_settings(s["id"])

				response["sounds_settings"] = consts.SOUNDS_SETTINGS

				socketio.emit('web_message', response)

			if action == "game_moves":
				response["game_moves"] = _dal.read_game_moves_by_id(message["id"])
				socketio.emit('web_message', response)

			if action == "remove_game":

				print(f'Request from client:{action}({message["id"]})')

				if _dal.remove_game_by_id(message["id"]):
					response["popup"] = "The game has been successfuly removed!"
				else:
					response["popup"] = "An error occured during the delete process!"

				socketio.emit('web_message', response)

		else:

			# Broadcast to all connected clients
			socketio.emit('request', message)

@appFlask.route("/")
def index():
	return render_template('2.0/index.html', data={"title":consts.WEB_NAME, "boardsize": 550, "iconsize": int(550/9)})
