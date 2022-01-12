# DGT Centaur mods

This project adds features to the DGT Centaur electronic chessboard, such as the ability to export your games via PGN files and use the chessboard as an interface for online play (e.g. Lichess)

Inside the DGT Centaur is a Raspberry Pi Zero with an SD Card, by replacing that with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and using our own software we get a wireless enabled chessboard that can theoretically do practically anything we can imagine. We've reversed engineered most of the protocols for for piece detection, lights, sound, and display (although we still occassionally discover the odd new thing). Now we can control the board, we're using that to create the software features.

**A word of caution!**

**All functionality is based on the fact that the Raspberry Pi Zero inside the board is being replaced with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and this breaks the product warranty. Proceed at your own risk!**

## Project Status and a Word on Forks and Derivatives and other builds

Note on forks and derivatives. As an open source project we want people to be able to take this code and work with it to improve people's experiences with electronic chess boards. You are welcome to amend the code, to use the reversed protocols, to create derivatives, and we encourage you to do so. Whilst we work with the DGT Centaur, maybe you will want to integrate it into your own DIY chessboard, and so on. Hopefully you'll feed back those great changes, fixes, improvements too. We ask only that you follow the license, be clear that your work is a modification, and you ensure that the end user understands the state of the code.

This project is presented to you in an alpha state. It is one where if you modify certain aspects of the code then it is possible to permanently break your board or the boards of others. We have spent quite literally 1000s of hours reverse engineering the code to understand it. When making a fork and derivative - please be very careful if you touch and modify code related to board communication.

If you have difficulties setting the code up, want to suggest features, need help, or to work a bug, let us know and we'll work with you. That's how it's worked in the past. We don't work in a directed way on any projects other than this one though. We are aware that there is a slightly modified build of this software presented in two ways that claim officialness: There is no other official build or install method other than the way we describe below. At the moment you can't simply burn an image of our software officially, which means our userbase has some specific technical skills to get it installed. They know what to expect, and have the skills to work with us if there is a problem. As time goes on, things will get easier and easier and that will be expanded out. If a retailer installs the code for you onto your board - whether it is called "final release" or not, they are installing a slightly modified version of alpha code. If you are downloading an image elsewhere that makes it easy to install and put it on your board, then regardless of how that image is presented, you are installing a slightly modified version of this alpha code. We'd like your experience with our software to be a positive one, which means that it should be clear what you should expect. In alpha, you will experience problems and bugs. Some of them could be signficant. Please be exceptionally carefully if you choose to install anything or have anything installed that claims to be anything else than alpha code and be sure you know what you are installing.

In other words we want people to be able to do everything open source provides the opportunity for, that's cool. We encourage that wholehearedly. But be sure to follow the license and be clear with the end user what they're getting.

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
Use the tool in tools/card-setup-tol. Follow this wiki page. (to be filled)

## Original centaur software

You might ask, what about my original centaur software. For copyrights purposes, we don't integrate that software togheter with ours. It is up to end user to move it on the new Raspberry Pi. Also the tool from tools/card-setup-tool is able to extract the centaur software from original card.
Use ssh connection to copy the software over. Pay attention that the the `/home/pi/centaur` already exists. Do not overwrite the files inside of it. Set the correct permissions: `chown -R pi.root /home/pi/centaur`

## Support

Join us on Discord: https://discord.gg/zqgUGK2x49

## Contributors welcome!

If you can offer some time and effort to the project please get in contact! Everybody is more than welcome!
