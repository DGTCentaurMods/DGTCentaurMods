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

import chess, random, time

from DGTCentaurMods.classes import Log
from DGTCentaurMods.classes.Plugin import Plugin, Centaur, TAnalyseResult
from DGTCentaurMods.consts import Enums, fonts

from typing import Optional, Tuple, List

EL_PROFESSOR:str = "El Professor"
BEST_MOVES_SCORE_DELTA:int = 30

GAME_MODES = (_EASY, _NORMAL, _EXPERT) = range(0,3)
MODE_CAPTIONS = ("Easy", "Normal", "Expert")
MODE_DETAILS = ("can blunder", "is inaccurate", "is quite good")

MATE_SCORE=100000

print = Centaur.print

class ElProfessor(Plugin):

    _mode = _EASY

    _analysis_in_progress:bool = False

    _candidate_moves:List[TAnalyseResult] = []
    _best_moves:List[TAnalyseResult] = []

    _try:int = 0

    # This function is automatically invoked each
    # time the player pushes a key.
    # Except the BACK key which is handled by the engine.
    def key_callback(self, key:Enums.Btn):

        # If the user pushes HELP,
        # we display the current best moves.
        if key == Enums.Btn.HELP:

            if not self._analysis_in_progress and self.chessboard.turn == self.HUMAN_COLOR and len(self._best_moves):
                Centaur.light_moves(tuple(m.uci_move for m in self._best_moves[:5]))
            else:
                Centaur.sound(Enums.Sound.WRONG_MOVE)
                return False

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

        # End game
        if event == Enums.Event.TERMINATION:

            if outcome.winner == self.HUMAN_COLOR:
                Centaur.sound(Enums.Sound.VICTORY)
                Centaur.messagebox(("YOU","WIN!",None))
            else:
                Centaur.sound(Enums.Sound.GAME_LOST)
                Centaur.messagebox(("YOU","LOOSE!",None))

        # New game
        if event == Enums.Event.NEW_GAME:
            pass

        # Player must physically play a move.
        if event == Enums.Event.PLAY:

            self._try = 0

            turn = self.chessboard.turn

            current_player = "You" if turn == chess.WHITE else EL_PROFESSOR

            # We display the board header.
            Centaur.header(
                text=f"{current_player} {'W' if turn == chess.WHITE else 'B'}",
                web_text=f"turn → {current_player} {'(WHITE)' if turn == chess.WHITE else '(BLACK)'}")

            def __analysis_callback(results: Tuple[TAnalyseResult, ...]):

                turn = self.chessboard.turn

                # Then we sort the list by score.
                # First items are always the better ones for human.
                candidate_moves:List[TAnalyseResult] = sorted(results, key=lambda x:x.score.pov(not turn))

                del results

                if len(candidate_moves):

                    Log.debug(f"Candidates -> {candidate_moves}")

                    # Computer turn?
                    if turn == (not self.HUMAN_COLOR):

                        # If expert mode or forced move
                        # we choose the unique move.
                        if self._mode == _EXPERT or len(candidate_moves) == 1:
                            Centaur.play_computer_move(candidate_moves[0].uci_move)

                        # If easy mode or if 1-3 candidates
                        # we choose a random candidate.
                        elif self._mode == _EASY or len(candidate_moves) <4:
                            Centaur.play_computer_move(candidate_moves[random.randint(0,len(candidate_moves)-1)].uci_move)

                        # If normal mode
                        # we choose a random candidate among the first half.
                        else:
                            Centaur.play_computer_move(candidate_moves[random.randint(0,int(len(candidate_moves)/2)-1)].uci_move)

                    else:

                        # The user can choose a move.
                        Centaur.messagebox(("Please","find a","good move!"))

                        best_score = candidate_moves[0].score.pov(turn).score(mate_score=MATE_SCORE)
        
                        score_delta = BEST_MOVES_SCORE_DELTA

                        # The more high is the score, the more high
                        # can be the delta.
                        if best_score>500:
                            score_delta = score_delta * int(best_score/500)

                        best_moves = list(filter(lambda move:best_score-move.score.pov(turn).score(mate_score=MATE_SCORE)<score_delta, candidate_moves))

                        self._candidate_moves.clear()
                        self._candidate_moves = candidate_moves

                        self._best_moves.clear()
                        self._best_moves = best_moves

                        Log.debug(f"Best moves : {self._best_moves}")

                self._analysis_in_progress = False

            # Computer turn?
            if turn == self.HUMAN_COLOR:
                Centaur.messagebox((EL_PROFESSOR,"is analyzing","the position..."))

            self._analysis_in_progress = True

            Centaur.request_chess_engine_evaluation(__analysis_callback, time=3, multipv=5)

    # When exists, this function is automatically invoked
    # when the player physically plays a move.
    def move_callback(self, uci_move:str, san_move:str, color:chess.Color, field_index:chess.Square):
        
        if color == self.HUMAN_COLOR:

            # If the analysis is not done, we force the move.
            if self._analysis_in_progress:

                Centaur.messagebox(("You", "forced the", f"move {san_move}!"))

                return True

            self._try += 1

            if uci_move in (m.uci_move for m in self._best_moves):

                if len(self._best_moves) == 1:
                    Centaur.messagebox(("YES", "The unique", "good move!"))
                else:
                    Centaur.messagebox(("YES!", "You found a", "good move!"))

                Centaur.sound(Enums.Sound.VERY_GOOD_MOVE, override=Enums.Sound.CORRECT_MOVE)

                return True

            # Player move is not within the Stockfish best candidates.
            # Maybe the move is one of the other guys...
            if uci_move in (m.uci_move for m in self._candidate_moves):
                Centaur.messagebox(("Correct", "You found", "a move!"))
                return True

            print(f"TRY #{self._try}", row=3)

            if self._try == 1:
                Centaur.messagebox(("This is a", "Bad move!", "Try again!"))

            if self._try == 2:
                Centaur.messagebox(("Incorrect!", "Choose", "another one!"))
            
            # Try #3 -> We show candidates.
            if self._try >= 3:
                Centaur.messagebox(("You failed!", "Pick one of", "the moves!"))

                four_moves = list(m.uci_move for m in self._candidate_moves[:4])
                random.shuffle(four_moves)

                #TODO to be reviewed
                # Call is delayed since the board will show the wrong move.
                Centaur.delayed_call(
                    lambda:Centaur.light_moves(tuple(four_moves)), 2)
                
            Centaur.sound(Enums.Sound.BAD_MOVE, override=Enums.Sound.WRONG_MOVE)

            return False
        
        # If the analysis is not done, we force the move.
        if self._analysis_in_progress:
            Centaur.messagebox(("You", "forced the", f"move {san_move}!"))

        # Computer move is always accepted.
        return True

     # When exists, this function is automatically invoked
     # at start, after splash screen, on PLAY button.
    def on_start_callback(self, key:Enums.Btn) -> bool:

        if key == Enums.Btn.UP:
            self.HUMAN_COLOR = chess.WHITE

        elif key == Enums.Btn.DOWN:
            self.HUMAN_COLOR = chess.BLACK
            # If computer is white, we reverse the screen.
            Centaur.reverse_board()

        elif key == Enums.Btn.TICK:

            Centaur.sound(Enums.Sound.COMPUTER_MOVE)
            self._mode += 1
            if self._mode == len(GAME_MODES):
                self._mode = 0

            # Selected game mode.
            print(MODE_CAPTIONS[self._mode], row=9, font=fonts.MEDIUM_MAIN_FONT)
            print(MODE_DETAILS[self._mode], row=11.5, font=fonts.SMALL_MAIN_FONT)

            # We do not start the game yet.
            return False

        else:
            # User must choose a color.
            return False
        
        Centaur.set_chess_engine("stockfish")
        Centaur.configure_chess_engine({"UCI_Elo": 2200})

        # Start a new game.
        Centaur.start_game(
            white="You", 
            black=EL_PROFESSOR, 
            event="Bots chess event 2024",
            flags=Enums.BoardOption.EVALUATION_DISABLED | Enums.BoardOption.CAN_FORCE_MOVES | Enums.BoardOption.CAN_UNDO_MOVES | Enums.BoardOption.PARTIAL_PGN_DISABLED)
        
        # Game started.
        return True

     # When exists, this function is automatically invoked
     # when the plugin starts.
    def splash_screen(self) -> bool:

        button = Centaur.print_button_label

        Centaur.clear_screen()

        print(EL_PROFESSOR, font=fonts.PACIFICO_FONT, row=1)

        print("Your chess", font=fonts.SMALL_MAIN_FONT, row=3)
        print("teacher", font=fonts.SMALL_MAIN_FONT)

        button(Enums.Btn.UP, x=6, text="Play white")
        button(Enums.Btn.DOWN, x=6, text="Play black")

        print()

        button(Enums.Btn.TICK, x=24, text="Mode")
        print(EL_PROFESSOR, row=10.5, font=fonts.SMALL_MAIN_FONT)

        button(Enums.Btn.BACK, row=13.5, x=6, text="Back home")

        Centaur.push_button(Enums.Btn.TICK)

        # The splash screen is activated.
        return True