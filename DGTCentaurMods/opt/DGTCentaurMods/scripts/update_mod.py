#!/usr/bin/python3 
import requests, os

from DGTCentaurMods.consts import consts
from DGTCentaurMods.classes import Log, SocketClient

SOCKET = SocketClient.get()

latest_release_url = ""

Log.info("Starting mod update...")
Log.info("Checking for the latest release...")

SOCKET.send_message({"popup":"Starting mod update!", "standby":True})

response = requests.get(consts.GITHUB_URI)

# if file was downloaded
if response.status_code == 200:
    response_json = response.json()
    latest_release_url = response_json['assets'][-1]['browser_download_url']
    Log.info(f"Latest release found: {latest_release_url}")
else:
    Log.exception(f"Internet down? Status code: {response.status_code}")
    exit(-1)

filename = latest_release_url.split('/')[-1]

Log.info("Cleaning previous deb files...")
os.system("sudo rm -f /home/pi/*.deb >/dev/null 2>&1")

Log.info(f"Downloading '{latest_release_url}'...")
os.system(f"wget {latest_release_url}")

Log.info("DPKG configuration..")
os.system("sudo sudo dpkg --configure -a")

SOCKET.send_message({"popup":"Installing new package!"})

Log.info("Uninstalling current version...")
os.system("sudo apt remove -y dgtcentaurmods")

Log.info("Installing package...")
os.system(f"sudo apt install -y ./{filename}")

Log.info("Rebooting!")
os.system("sudo reboot")