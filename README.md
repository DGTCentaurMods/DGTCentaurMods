# DGT Centaur mods

This project adds features to the DGT Centaur electronic chessboard, such as the ability to export your games via PGN files and use the chessboard as an interface for online play (e.g. Lichess)

Inside the DGT Centaur is a Raspberry Pi Zero with an SD Card, by replacing that with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and using our own software we get a wireless enabled chessboard that can theoretically do practically anything we can imagine. We've reversed engineered most of the protocols for for piece detection, lights, sound, and display (although we still occassionally discover the odd new thing). Now we can control the board, we're using that to create the software features.

**A word of caution!**

**All functionality is based on the fact that the Raspberry Pi Zero inside the board is being replaced with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and this breaks the product warranty. Proceed at your own risk!**

## Project status

Currently everything is to be considered a **work in progress**, as there aren't any plug'n'play images to be used and you need to tinker quite a bit with the board. We're currently working on a build process to make it easier for devs and end users

## Current features

eBoard Emulation - Revelation II. Enables you to use the DGT Centaur as if it was a bluetooth DGT eboard with apps, rabbit plugin, Livechess, etc

Online Gameplay - Lichess (can be buggy)

Web Interface - Shows live view of chessboard in a browser

PGN Download - For all played games from web interface

Game Analysis - Simple playback/analysis of played games from web interface.

Streaming Video - On the web interface /video provides a live mjpeg stream (for example for live streaming in OBS)

Chromecast - Stream live board view to Chromecast

Wifi - Capability to join wifi from the board (WPS/WPA2)

Play Engines - Stockfish (without centaur adaptive mode), ct800

## Roadmap

Currently we are working on...
1. Enhancing board emulation support
2. Builds/Releases/Installation method
3. Squashing bugs
4. Choose what engines you want to play
5. Configuration options
6. Admiring the fact that the DGT centaur is now the most awesome electronic chess board available :)

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
