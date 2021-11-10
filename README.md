# DGT Centaur mods

This project adds features to the DGT Centaur electronic chessboard, such as the ability to export your games via PGN files and use the chessboard as an interface for online play (e.g. Lichess)

Inside the DGT Centaur is a Raspberry Pi Zero with an SD Card, by replacing that with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and using our own software we get a wireless enabled chessboard that can theoretically do practically anything we can imagine. We've reversed engineered most of the protocols for for piece detection, lights, sound, and display (although we still occassionally discover the odd new thing). Now we can control the board, we're using that to create the software features.

**A word of caution!**

**All functionality is based on the fact that the Raspberry Pi Zero inside the board is being replaced with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and this breaks the product warranty. Proceed at your own risk!**

## Project status

Currently everything is to be considered in alpha

## Current features

eBoard Emulation - DGT Revelation II - Enables you to use the DGT Centaur as if it was a bluetooth DGT eboard with apps, rabbit plugin, Livechess, etc. Millennium (Bluetooth Classic) - Works with Chess for Android, Chess.com app on android (experimental)

Online Gameplay - Lichess (set Lichess API token from the web interface) then play from the board.

Web Interface - on http://ipaddress:5000 Shows live view of chessboard in a browser

PGN Download - For all played games from web interface

Game Analysis - Simple playback/analysis of played games from web interface.

Streaming Video - On the web interface /video provides a live mjpeg stream (for example for live streaming in OBS)

Chromecast - Stream live board view to Chromecast

Wifi - Capability to join wifi from the board (WPS/WPA2)

Play Engines - Stockfish (without centaur adaptive mode), ct800 . Upload your own engines from the web interface.

General Settings - Connect Wifi, Pair bluetooth, sound, lichess api token

## Roadmap

Currently we are working on...
1. Builds/Releases
2. Squashing bugs
3. BLE boards emulation
4. Improving Gamemanager features (gamemanager is the central system that handles chess games)
5. Code tidyup
6. Instructions
7. Admiring the fact that the DGT centaur is now the most awesome electronic chess board available :)

## Installation notes

In order to run the project on a Raspberry Pi Zero W, these are some steps to be completed:

1. Root the Raspberry Pi Zero that comes with the board and backup the `/home/pi/centaur` folder somewhere
2. Get a Raspberry Pi Zero W and flash the Rasberry Pi OS Lite image on its SD card
3. Configure access to your wi-fi network and enable SSH access to the Pi (please refer to the official docs)
4. Add `dtparam-spi=on`, `enable_uart=1`, and `dtoverlay=spi1-3cs` to /boot/config.txt of the Pi Zero W in order to enable the serial interface
5. Copy the `centaur` folder in `/home/pi`
6. Copy the project files in home dir
7. Edit `/etc/rc.local` to launch `menu.py` at startup
8. Install `libtiff5` via apt
9. Ensure pip3 is available on the system or install it via apt
10. Install the required libraries in requirements.txt `pip3 install -r requirements.txt`
11. Reboot

You should then be ready to connect to the board via SSH and tinker with it!

## Support

Join us on Discord: https://discord.gg/zqgUGK2x49

## Contributors welcome!

If you can offer some time and effort to the project please get in contact! Everybody is more than welcome!
