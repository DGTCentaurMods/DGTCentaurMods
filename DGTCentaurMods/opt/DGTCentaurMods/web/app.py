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
from DGTCentaurMods.consts import consts
from DGTCentaurMods.classes import DAL
from DGTCentaurMods.classes.CentaurConfig import CentaurConfig

import os, time, logging, subprocess

#logging.getLogger('chess.engine').setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").propagate = False

appFlask = Flask(__name__)

socketio = SocketIO(appFlask, cors_allowed_origins="*")

if __name__ == '__main__':
	print("Starting socketio server...")
	#socketio.run(appFlask, port=5000, host='0.0.0.0', ssl_context='adhoc', allow_unsafe_werkzeug=True)
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


	if "web_menu" in message:

		response["update_menu"] = [{"label":f"The {consts.MAIN_ID} service is not properly running, please check!", "action":{ "type": "js", "value": '() => null' }}]

		socketio.emit('message', response)

	# Script request
	if "script" in message:
		script = message["script"]

		try:
			result = subprocess.check_output(["python3", f"{consts.OPT_DIRECTORY}/scripts/{script}.py"])

			response["script_output"] = result.decode()
			socketio.emit('message', response)
		
		except Exception as e:
			response["script_output"] = str(e)
			socketio.emit('message', response)
			
			pass

	# System request
	if "sys" in message:
		action = message["sys"]

		if action == "homescreen":
			# We relay the message to the app
			socketio.emit('request', message)

		if action == "centaur":

			os.system(f"sudo systemctl stop {consts.MAIN_ID}.service")

			time.sleep(.5)
			os.chdir(f"{consts.HOME_DIRECTORY}/centaur")
			os.system("sudo ./centaur")

		if action == "shutdown":
			# We relay the message to the app
			socketio.emit('request', message)
			os.system("sudo pkill centaur")
			time.sleep(4)
			os.system("sudo poweroff")

		if action == "reboot":
			# We relay the message to the app
			socketio.emit('request', message)
			os.system("sudo pkill centaur")
			time.sleep(.5)
			os.system("sudo reboot")

		if action == "restart_service":
			os.system("sudo pkill centaur")
			time.sleep(.5)
			os.system(f"sudo systemctl restart {consts.MAIN_ID}.service")

		if action == "restart_web_service":
			os.system("sudo pkill centaur")
			time.sleep(.5)
			os.system(f"sudo systemctl restart {consts.MAIN_ID}Web.service")

		if action == "log_events":
			response["log_events"] = common.tail(open(consts.LOG_FILENAME, "r"), 500)
			socketio.emit('message', response)

	else:

		_get_file_descriptor = lambda action:{
			"plugin":{
				"directory":f"{consts.OPT_DIRECTORY}/plugins",
				"label":"plugin script",
				"extension":"py",
				"editable_name":True,
				"can_delete":False,
			},
			"uci":{
				"directory":f"{consts.OPT_DIRECTORY}/engines",
				"label":"UCI File",
				"extension":"uci",
				"editable_name":False,
				"can_delete":False,
			},
			"famous_pgn":{
				"directory":f"{consts.OPT_DIRECTORY}/famous_pgns",
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
				
				socketio.emit('message', response)
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
					socketio.emit('message', response)

					return
				
				if action["new_file"] == "__delete__" and file_descriptor["can_delete"]:

					os.system(f'sudo rm -f "{path}"')

					response["popup"] = "The " + file_descriptor["label"] + " has been successfuly deleted!"
					socketio.emit('message', response)

					return

				f = open(path, "w")

				f.write(action["text"])
				f.close()

				if action["new_file"] != action["file"]:
					newpath = file_descriptor["directory"]+'/'+action["new_file"]+'.'+file_descriptor["extension"]
					os.system(f'sudo mv "{path}" "{newpath}"')

				response["popup"] = "The " + file_descriptor["label"] + " has been successfuly updated!"
				socketio.emit('message', response)
			return
		
		if "data" in message:
			action = message["data"]

			_dal = DAL.get()

			if action == "previous_games":
				response["previous_games"] = _dal.get_all_games()
				socketio.emit('message', response)

			if action == "sounds_settings_set":

				if "value" in message:
					CentaurConfig.update_sound_settings(message["value"]["id"], message["value"]["value"])

			if action == "sounds_settings":
				
				# We read the sounds settings
				for s in consts.SOUNDS_SETTINGS:
					s["value"] = CentaurConfig.get_sound_settings(s["id"])

				response["sounds_settings"] = consts.SOUNDS_SETTINGS

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