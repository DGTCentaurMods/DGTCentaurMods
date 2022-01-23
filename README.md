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

## Install procedure
See the install procedure in the release info page.

## Support

Join us on Discord: https://discord.gg/zqgUGK2x49

## Contributors welcome!

If you can offer some time and effort to the project please get in contact! Everybody is more than welcome!
