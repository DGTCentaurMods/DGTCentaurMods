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

LEGACY MODULES ARE NO MORE REACHABLE USING THIS SOFTWARE.

## Roadmap

Currently we are working on...
1. Squashing bugs
2. Improving performance
3. Adding new features

## Install procedure
See the install procedure in the release info page.
This fork is initially based against the
[v1.2.1 original version](https://github.com/EdNekebno/DGTCentaurMods/releases/tag/v1.2.1).

## This project uses...

- [Python 3](https://www.python.org/)
- [e-Paper](https://github.com/waveshareteam/e-Paper)
- [Pillow](https://pypi.org/project/Pillow/)
- [wpa-pyfi](https://pypi.org/project/wpa-pyfi/)
- [python-chess](https://python-chess.readthedocs.io/)
- [berserk](https://pypi.org/project/berserk/)
- [AngularJS](https://angularjs.org/)
- [chessboard.js](https://chessboardjs.com/)
- [Flask](https://flask.palletsprojects.com/)
- [flask-socketio](https://flask-socketio.readthedocs.io/)
- Multiple chess engines
- DGT Centaur board Reverse engineering work of the [original](https://github.com/EdNekebno/DGTCentaurMods) project

## Contributors welcome!

If you can offer some time and effort to the project please get in contact! Everybody is more than welcome!

![](https://images2.imgbox.com/4f/0f/TA6NrpFN_o.jpg)

