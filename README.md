# DGT Centaur mods (Alistair's version)

<img src="https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/screenshots/shot_1.jpg?raw=true" style="width:75%"/>

The [original](https://github.com/EdNekebno/DGTCentaurMods) DGT Centaur mods project adds features to the DGT Centaur electronic chessboard.

Inside the DGT Centaur is a Raspberry Pi Zero with an SD Card, by replacing that with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and using a modified software, we get a wireless enabled chessboard that can theoretically do practically anything we can imagine.

**This current project overrides the legacy one, re-coding and re-factoring all the unstable scripts, adding new features.**

**A word of caution!**

**All functionality is based on the fact that the Raspberry Pi Zero inside the board is being replaced with a Raspberry Pi Zero 2 W (or Raspberry Pi Zero W) and this breaks the product warranty. Proceed at your own risk!**

## Current features

- New Centaur screen interface.

- New web remote control to pilot the board from a browser (You can even play from the web interface).

- New advanced web Interface - on http://IP_ADDRESS or the hostname of you board.

- You can takeback all the moves (as the original Centaur software).

- You can force the opponent moves (as the original Centaur software).

- You can resume the last engine or 1 vs 1 game you played.

- New "Famous!" module that allows to train against famous games.

- New Lichess module.

- New WIFI module.
  
- New Plugins engine with several plugin samples.
The plugin engine offers the possibility to easily create and deploy new modules to the Centaur.

- Live script interface to create macros and "automate" all the usage of the board.

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

## Few screenshots of the web UI

<img src="https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/screenshots/shot_2.jpg?raw=true" style="width:75%"/>
<img src="https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/screenshots/shot_3.jpg?raw=true" style="width:50%"/>

## Plugin creation

If you know a bit Python, you can easily create new plugins and play with them. New plugins are dynamically recognized as soon as they are copied within the "plugins" directory.

Few examples of plugins are available, they show the basic structure of a plugin.

- "SQuiz" is a plugin that allows the player to memorize the squares of the chessboard.
- "Althoff bot" is an adaptative bot that can make blunders and update its level according to the position evaluation.

Here is an example of a "Random bot" that plays random moves:

```python
import chess, random

from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts

from typing import Optional

HUMAN_COLOR = chess.WHITE

# The plugin must inherits of the Plugin class.
# Filename must match the class name.
class RandomBot(Plugin):

    # This function is automatically invoked each
    # time the player pushes a key.
    # Except the BACK key which is handled by the engine.
    def key_callback(self, key:Enums.Btn) -> bool:

        # If the user pushes HELP,
        # we display an hint using Stockfish engine.
        if key == Enums.Btn.HELP:
            Centaur.hint()

            # Key has been handled.
            return True
        
        # Key can be handled by the engine.
        return False
        
    # When exists, this function is automatically invoked
    # when the game engine state is affected.
    def event_callback(self, event:Enums.Event, outcome:Optional[chess.Outcome]):

        # If the user chooses to leave,
        # we quit the plugin.
        if event == Enums.Event.QUIT:
            self.stop()

        if event == Enums.Event.PLAY:

            turn = self.chessboard.turn

            current_player = "You" if turn == chess.WHITE else "Random bot"

            # We display the board header.
            Centaur.header(f"{current_player} {'W' if turn == chess.WHITE else 'B'}")

            if turn == (not HUMAN_COLOR):

                # We choose a random move
                uci_move = str(random.choice(list(self.chessboard.legal_moves)))

                Centaur.play_computer_move(uci_move)

    # When exists, this function is automatically invoked
    # at start, after splash screen, on PLAY button.
    def on_start_callback(self, key:Enums.Btn) -> bool:

        # Start a new game.
        Centaur.start_game(
            white="You", 
            black="Random bot", 
            event="Bots chess event 2024",
            flags=Enums.BoardOption.CAN_UNDO_MOVES)
        
        # Game started.
        return True

    # When exists, this function is automatically invoked
    # when the plugin starts.
    def splash_screen(self) -> bool:

        print = Centaur.print

        Centaur.clear_screen()

        print("RANDOM", row=2)
        print("BOT", font=fonts.DIGITAL_FONT, row=4)
        print("Push PLAY", row=8)
        print("to")
        print("start")
        print("the game!")

        # The splash screen is activated.
        return True
```

## Live script module

A sample of live script is available within the "scripts" directory.

Here is a simple macro that plays against the Random bot:

```python
from DGTCentaurMods.classes import LiveScript, CentaurScreen
from DGTCentaurMods.consts import Enums

import time, random

SCREEN = CentaurScreen.get()
LS = LiveScript.get()

# Back to home menu
LS.push_button(Enums.Btn.BACK)
LS.push_button(Enums.Btn.BACK)
LS.push_button(Enums.Btn.BACK)
LS.push_button(Enums.Btn.BACK)

def play_random_move():
  legal_moves = LS.chessboard().legal_moves
  uci_move = str(random.choice(list(legal_moves)))[0:4]
  return LS.play(uci_move)

# Choose PLUGINS
LS.select_menu("PLUGINS")

# Launch Random bot plugin
LS.select_menu("RANDOM BOT")
time.sleep(2)

# Pass the splash screen
LS.push_button(Enums.Btn.PLAY)
time.sleep(2)

# Random moves
for _ in range(10):
  play_random_move()
  bot_move = LS.waitfor_computer_move()
  LS.play(bot_move)

SCREEN.write_text(4, "SCRIPT")
SCREEN.write_text(5, "DONE!")
```

