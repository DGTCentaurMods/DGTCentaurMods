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

from pathlib import Path
import requests, os, socketio

HOME_DIRECTORY = str(Path.home())
MAIN_ID = "DGTCentaurMods"
GITHUB_URI = "https://api.github.com/repos/Alistair-Crompton/DGTCentaurMods/releases/latest"

sio = socketio.Client()

try:
    sio.connect('http://localhost')
except:
    sio = None
    pass

latest_release_url = ""

print("Starting mod update...")
print("Checking for the latest release...")

if sio:
    sio.emit('request', {"screen_message":"Update started!"})

response = requests.get(GITHUB_URI)

# if file was downloaded
if response.status_code == 200:
    response_json = response.json()
    latest_release_url = response_json['assets'][-1]['browser_download_url']
    print(f"Latest release found: {latest_release_url}")
else:
    print(f"Internet down? Status code: {response.status_code}")
    
    if sio:
        sio.emit('request', {"screen_message":"Update failed!"})
    exit(-1)

filename = latest_release_url.split('/')[-1]

print("Cleaning previous deb files...")
os.system(f"sudo rm -f {HOME_DIRECTORY}/*.deb >/dev/null 2>&1")

if sio:
    sio.emit('request', {"screen_message":"Downloading..."})
    sio.disconnect()

print(f"Downloading '{latest_release_url}'...")
os.system(f"wget -O {HOME_DIRECTORY}/{MAIN_ID}_latest.deb {latest_release_url}")

print("Rebooting!")
os.system("sudo reboot")