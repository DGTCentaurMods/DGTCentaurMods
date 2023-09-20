# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

import chess, random

from DGTCentaurMods.classes.Plugin import Plugin, Centaur
from DGTCentaurMods.consts import Enums, fonts

QUESTIONS_COUNT:int = 20

# The plugin must inherits of the Plugin class.
# Filename must match the class name.
class Squiz(Plugin):

    # Constructor for initialization stuff
    # The id is the name of the plugin/class
    def __init__(self, id:str):
        super().__init__(id)

        self.initialize()

    # Initialization function,
    # invoked on each new game.
    def initialize(self):
        self._qindex:int = 0
        self._bonus:int = QUESTIONS_COUNT*3

        # Plugin is paused - the player needs to push PLAY.
        Centaur.pause_plugin()

    # Game ends.
    def game_over(self):

        print = Centaur.print

        Centaur.clear_screen()

        print("GAME", row=2, font=fonts.DIGITAL_FONT)
        print("OVER", row=4, font=fonts.DIGITAL_FONT)
    
        print("SCORE", row=7)

        score = int(self._bonus * 100 / (QUESTIONS_COUNT*3))

        print('%'+str(score), font=fonts.DIGITAL_FONT)

        print("Press PLAY", row=11)
        print("To retry!")

        self.initialize()

    # Generate a new question,
    # choosing a random square then displaying it.
    def generate_question(self):

        # Next question...
        self._qindex += 1

        # Do we reach the limit?
        if self._qindex == QUESTIONS_COUNT+1:
            self.game_over()
            return

        print = Centaur.print

        Centaur.clear_screen()

        # We create a random square.
        # The square_name function needs a number from 0 to 63.
        self._random_square = chess.square_name(random.randint(0,63))

        print("Question", row=2)
        print(str(self._qindex), font=fonts.DIGITAL_FONT)

        print("Please place", row=5)
        print("a piece on")
        print()
        print(self._random_square, font=fonts.DIGITAL_FONT)

    """
    
    # This function is automatically invoked when
    # the user launches the plugin.
    def start(self):

        # The plugin starts.
        super().start()

    # This function is (automatically) invoked when
    # the user stops the plugin.
    def stop(self):

        # Back to the main menu.
        super().stop()

    """

    # This function is automatically invoked each
    # time the player pushes a key.
    # Except the BACK key which is handled by the engine.
    def key_callback(self, key:Enums.Btn):

        # If the user press HELP,
        # we display the correct square.
        if key == Enums.Btn.HELP:
            Centaur.sound(Enums.Sound.TAKEBACK_MOVE)
            Centaur.flash(self._random_square)

    # When exists, this function is automatically invoked each
    # time the player moves a piece.
    def field_callback(self,
                square:str,
                field_action:Enums.PieceAction,
                web_move:bool):

        # We care only when the user drop a piece.
        if field_action == Enums.PieceAction.PLACE:

            Centaur.flash(square)

            # Correct answer?
            if self._random_square == square:
                Centaur.sound(Enums.Sound.CORRECT_MOVE)

                # Next question...
                self.generate_question()

            else:
                Centaur.sound(Enums.Sound.WRONG_MOVE)
                Centaur.print("WRONG!", row=11)

                # Wrong answer, we decrease the bonus.
                self._bonus -= 1

                if self._bonus == 0:
                    self.game_over()

     # When exists, this function is automatically invoked
     # at start, after splash screen, on PLAY button.
    def on_start_callback(self, key:Enums.Btn) -> bool:

        Centaur.sound(Enums.Sound.COMPUTER_MOVE)
        self.generate_question()

        # Game started.
        return True

     # This function is automatically invoked
     # when the plugin starts.
    def splash_screen(self) -> bool:

        print = Centaur.print

        Centaur.clear_screen()

        print("SQUIZ", font=fonts.DIGITAL_FONT, row=2)
        print("Push PLAY", row=5)
        print("to")
        print("start")
        print("the game!")

        # The splash screen is activated.
        return True