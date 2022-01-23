# DGT Centaur mods

This project adds features to the DGT Centaur electronic chessboard, such as the ability to export your games via PGN files, use the chessboard as an interface for online play (e.g. Lichess), play engines, and emulate other chess boards such as the DGT Pegasus.

Inside the DGT Centaur is a Raspberry Pi Zero with an SD Card, by replacing that with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and using our own software we get a wireless enabled chessboard that can theoretically do practically anything we can imagine. We've reversed engineered most of the protocols for for piece detection, lights, sound, and display (although we still occassionally discover the odd new thing). Now we can control the board, we're using that to create the software features.

**A word of caution!**

**All functionality is based on the fact that the Raspberry Pi Zero inside the board is being replaced with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and this breaks the product warranty. Proceed at your own risk!**

## Project Status and a Word on Forks and Derivatives and other builds

Note on forks and derivatives. As an open source project we want people to be able to take this code and work with it to improve people's experiences with electronic chess boards. You are welcome to amend the code, to use the reversed protocols, to create derivatives, and we encourage you to do so. Whilst we work with the DGT Centaur, maybe you will want to integrate it into your own DIY chessboard, and so on. Hopefully you'll feed back those great changes, fixes, improvements too. We ask only that you follow the license, be clear that your work is a modification, and you ensure that the end user understands the state of the code.

This project is presented to you in an beta state. This means that whilst the project works generally, you may come across some bugs. If you have problems, feel free to raise an issue or join us on discord https://discord.gg/zqgUGK2x49 .

## Current features

eBoard Emulation - DGT Revelation II - Enables you to use the DGT Centaur as if it was a bluetooth DGT eboard with apps, rabbit plugin, Livechess, etc. Millennium (Bluetooth Classic) - Works with Chess for Android, Chess.com app on android (experimental)

DGT Pegasus - Emulate a DGT Pegasus. Works with the DGT Chess app

Online Gameplay - Lichess (set Lichess API token from the web interface) then play from the board.

Web Interface - on http://ipaddress:5000 Shows live view of chessboard, settings, and the other features below

PGN Download - For all played games from web interface

Game Analysis - Simple playback/analysis of played games from web interface.

Streaming Video - On the web interface /video provides a live mjpeg stream (for example for live streaming in OBS)

Chromecast - Stream live board view to Chromecast

Wifi - Capability to join wifi from the board (WPS/WPA2)

Play Engines - Stockfish (without centaur adaptive mode), ct800, zahak, rodentIV, maia . Upload your own engines from the web interface.

General Settings - Connect Wifi, Pair bluetooth, sound, lichess api token

## Roadmap

Currently we are working on...
1. Squashing bugs
2. Emulating more BLE boards (currently Pegasus is done)
3. Improving Gamemanager features (gamemanager is the central system that handles chess games)
4. Code tidyup
5. Instructions
6. Other stuff :)

## Manual installation

In order to run the project on a Raspberry Pi Zero W, these are some steps to be completed:

1. Get a Raspberry Pi Zero W and flash the Rasberry Pi OS Lite image on its SD card
3. Configure access to your wi-fi network and enable SSH access to the Pi (please refer to the official docs)
4. Update the OS: `sudo apt -y update` `sudo apt -y upgrade` `sudo apt -y full-upgrade`
5. Install git tool: `apt -y install git`
6. Clone this repo: `git clone https://github.com/EdNekebno/DGTCentaur`
7. Build a deb package: `cd DGTCentaur/build` `./build.sh master` to build from master branch. Make syre to INCLUDE Stockfish into the build.
9. When previous step is done you should have the deb file in current folder. Go ahead and install it: `sudo apt -y install ./<deb_file>`
Installation process takes some time, so sit back and have a beer. Once done, reboot your Raspberry Pi. If all went well, board should power on and the new DGTCentaurMods will start. You'll notice the menu on the display.

## Automatic setup of SD card
Use the tool in tools/card-setup-tol. Follow the README section on tool's page.

## Original centaur software

You might ask, what about my original centaur software. For copyrights reasons, we don't integrate that software togheter with ours. It is up to end user to move it on the new Raspberry Pi. Also the tool from tools/card-setup-tool is able to extract the centaur software from original card.
Use ssh connection to copy the software over. Pay attention that the the `/home/pi/centaur` already exists. Do not overwrite the files inside of it. Set the correct permissions: `chown -R pi.root /home/pi/centaur`

## Support

Join us on Discord: https://discord.gg/zqgUGK2x49

## Contributors welcome!

If you can offer some time and effort to the project please get in contact! Everybody is more than welcome!
