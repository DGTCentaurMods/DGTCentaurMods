#!/usr/bin/python3 
import requests, os

from DGTCentaurMods.consts import consts

import socketio

sio = socketio.Client()
sio.connect('http://localhost')

latest_release_url = ""

print("Starting mod update...")
print("Checking for the latest release...")

sio.emit('request', {"screen_message":"Update started!"})

response = requests.get(consts.GITHUB_URI)

# if file was downloaded
if response.status_code == 200:
    response_json = response.json()
    latest_release_url = response_json['assets'][-1]['browser_download_url']
    print(f"Latest release found: {latest_release_url}")
else:
    print(f"Internet down? Status code: {response.status_code}")
    sio.emit('request', {"screen_message":"Update failed!"})
    exit(-1)

filename = latest_release_url.split('/')[-1]

print("Cleaning previous deb files...")
os.system("sudo rm -f *.deb >/dev/null 2>&1")

sio.emit('request', {"screen_message":"Downloading..."})

print(f"Downloading '{latest_release_url}'...")
os.system(f"wget {latest_release_url}")

print("DPKG configuration..")
os.system("sudo sudo dpkg --configure -a")

sio.emit('request', {"screen_message":"Installing...", "standby":True})
sio.disconnect()

print("Uninstalling current version...")
os.system("sudo apt remove -y dgtcentaurmods")

print("Installing package...")
os.system(f"sudo apt install -y ./{filename}")

print("Rebooting!")
os.system("sudo reboot")