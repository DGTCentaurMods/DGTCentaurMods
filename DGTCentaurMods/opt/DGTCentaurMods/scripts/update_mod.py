#!/usr/bin/python3 
import requests
import subprocess

print("Cleaning old deb files")
subprocess.run(["rm", "*.deb"])

print("Uninstalling current version")
subprocess.run(["sudo", "apt", "-y", "remove", "dgtcentaurmods"])

latest_release_url = ''

print("Checking for the latest release")
response = requests.get("https://api.github.com/repos/Alistair-Crompton/DGTCentaurMods/releases/latest")

# if file was downloaded
if response.status_code == 200:
    response_json = response.json()
    latest_release_url = response_json['assets'][-1]['browser_download_url']
    print(f"Latest release found: {latest_release_url}")
else:
    print(f"Internet down? Status code: {response.status_code}")
    exit(-1)

filename = latest_release_url.split('/')[-1]

print(f"Downloading {latest_release_url}")
response = requests.get(latest_release_url)

# if file was downloaded
if response.status_code == 200:
    with open(f"{filename}", "wb") as file:
        file.write(response.content)
    print(f"{filename} saved")
else:
    print(f"Failed to download. Status code: {response.status_code}")


print("Installing package")
subprocess.run(["sudo", "apt", "--assume-yes", "install", f"./{filename}"])

print("Rebooting!")
subprocess.run(["sudo", "reboot", "now"])