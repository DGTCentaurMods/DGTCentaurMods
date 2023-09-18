# DGT Centaur mods (Alistair's version)

The [original](https://github.com/EdNekebno/DGTCentaurMods) DGT Centaur mods project adds features to the DGT Centaur electronic chessboard.

Inside the DGT Centaur is a Raspberry Pi Zero with an SD Card, by replacing that with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and using a modified software, we get a wireless enabled chessboard that can theoretically do practically anything we can imagine.

This current project overrides the legacy one, re-coding and re-factoring all the unstable scripts.

**A word of caution!**

**All functionality is based on the fact that the Raspberry Pi Zero inside the board is being replaced with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and this breaks the product warranty. Proceed at your own risk!**

## Current reworked features

- New Centaur interface.

- New advanced web Interface - on http://IP_ADDRESS or the hostname of you board.

- You can now takeback moves.

- You can force a move (if you play against an engine).

- You can resume the last engine or 1 vs 1 game you played.

- New "Famous!" module that allows to train against famous games.

- New Lichess module.

- New WIFI module.
  
- Plugins engine.

LEGACY MODULES ARE NO MORE REACHABLE USING THIS SOFTWARE.

## Roadmap

Currently we are working on...
1. Squashing bugs
2. Improving performance
3. Adding new features

## Install procedure
1. From your Pi, download the latest available release:

```
wget -O ./_DGTCentaurMods_A.alpha-latest.deb `curl -s https://api.github.com/repos/Alistair-Crompton/DGTCentaurMods/releases/latest | grep browser_download_url | cut -d '"' -f 4`
```

2. Install the downloaded package:

```
sudo apt install -y ./_DGTCentaurMods_A.alpha-latest.deb
```

## This project uses...

- [Python 3](https://www.python.org/)
- [Waveshare e-Paper driver](https://github.com/waveshareteam/e-Paper)
- [Pillow library](https://pypi.org/project/Pillow/)
- [python-chess library](https://python-chess.readthedocs.io/)
- [berserk library](https://pypi.org/project/berserk/)
- [AngularJS](https://angularjs.org/)
- [chessboard.js](https://chessboardjs.com/)
- [Flask server](https://flask.palletsprojects.com/)
- [flask-socketio library](https://flask-socketio.readthedocs.io/)
- [wpa-pyfi](https://pypi.org/project/wpa-pyfi/)
- Multiple chess engines
- DGT Centaur board Reverse engineering work of the [original](https://github.com/EdNekebno/DGTCentaurMods) project

## Support & Requests

You can send a mail to: dgtcentaurmods@moult.org.

## Contributors welcome!

If you can offer some time and effort to the project please get in contact! Everybody is more than welcome!

![](https://images2.imgbox.com/10/f5/CYVB5sgU_o.jpg)

