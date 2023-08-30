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

from DGTCentaurMods.game.classes import ChessEngine, DAL, Log, SocketClient, CentaurScreen, CentaurBoard
from DGTCentaurMods.game.classes.CentaurConfig import CentaurConfig
from DGTCentaurMods.game.consts import Enums, consts, fonts
from DGTCentaurMods.game.lib import common

#from pympler import muppy, summary

from threading import Thread, Event
import time, asyncio
import chess
import chess.pgn
import sys
import inspect
import re

CENTAUR_BOARD = CentaurBoard.get()
SCREEN = CentaurScreen.get()

# Game manager class
class Engine():

    _started = False

    _thread_is_alive = False
    _initialized = False
    _new_evaluation_requested = False

    _previous_move_displayed = False

    _chessboard = None

    _san_move_list = []

    _socket = None

    _show_evaluation = True

    def __init__(self, event_callback = None, move_callback = None, undo_callback = None, key_callback = None, flags = Enums.BoardOption.CAN_DO_COFFEE, game_informations = {}):

        SCREEN.clear_area()

        SCREEN.write_text(3,"Please place")
        SCREEN.write_text(4,"pieces in")
        SCREEN.write_text(5,"starting")
        SCREEN.write_text(6,"position!")

        self._key_callback_function = key_callback
        self._move_callback_function = move_callback
        self._undo_callback_function = undo_callback
        self._event_callback_function = event_callback

        self._game_informations = game_informations

        self.source = inspect.getsourcefile(sys._getframe(1))

        self._can_force_moves = Enums.BoardOption.CAN_FORCE_MOVES in flags
        self._can_undo_moves = Enums.BoardOption.CAN_UNDO_MOVES in flags

        self._evaluation_disabled = Enums.BoardOption.EVALUATION_DISABLED in flags
        self._show_evaluation = not self._evaluation_disabled

        db_record_disabled = Enums.BoardOption.DB_RECORD_DISABLED in flags

        self._partial_pgn_disabled = Enums.BoardOption.PARTIAL_PGN_DISABLED in flags

        self._dal = DAL.get()

        self._dal.set_read_only(db_record_disabled)

        #CENTAUR_BOARD.clear_serial()

    @staticmethod
    def __invoke_callback(callback, **args):
        if callback != None:
            try:
                Log.debug(f"{Engine.__invoke_callback.__name__}[{callback.__name__}({args})]")
                return callback(args)
            except Exception as e:
                Log.exception(Engine.__invoke_callback, e)
        else:
            return True

    def __initialize(self):

        CENTAUR_BOARD.leds_off()

        self._source_square = -1
        self._legal_squares = []
        self._computer_uci_move = ""
        self._is_computer_move = False
        self._undo_requested = False
        self._san_move_list = []

        self._new_evaluation_requested = False

    def __key_callback(self, key_index):

        if Engine.__invoke_callback(self._key_callback_function, key=key_index) == False:
            # Key has not been handled by the client!

            # Default tick key
            if not self._evaluation_disabled and key_index == Enums.Btn.TICK:
                self._show_evaluation = not self._show_evaluation

                self.update_evaluation()

                self.display_partial_PGN()
                self.display_board()

            # Default exit key
            if key_index == Enums.Btn.BACK:
                
                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.QUIT)

                self.stop()
        
            # Default down key: show previous move
            if key_index == Enums.Btn.DOWN:

                if self._previous_move_displayed:
                     
                     self._previous_move_displayed = False
                     
                     if self._is_computer_move:
                        self.set_computer_move()
                          
                     else:
                        CENTAUR_BOARD.leds_off()

                else:
                    # We read the last move that has been recorded
                    previous_uci_move = self.get_last_uci_move()

                    if previous_uci_move:
                        from_num = common.Converters.to_square_index(previous_uci_move, Enums.SquareType.ORIGIN)
                        to_num = common.Converters.to_square_index(previous_uci_move, Enums.SquareType.TARGET)

                        CENTAUR_BOARD.led_from_to(from_num,to_num)

                        self._previous_move_displayed = True
                

    # Receives field events from the board.
    # Positive is a field lift, negative is a field place.
    # Numbering 0 = a1, 63 = h8
    def __field_callback(self, field_index, field_action):

        if self._initialized == False:
            return

        self._previous_move_displayed = False

        try:
            # We do not need to check the reset if a piece is lifted
            self._need_starting_position_check = False

            # Check the piece colour against the current turn
            piece_color_is_consistent = self._chessboard.turn == self._chessboard.color_at(field_index)
            
            square_name = common.Converters.to_square_name(field_index)
      
            Log.debug(f"field_index:{field_index}, square_name:{square_name}, piece_action:{field_action}")

            # Legal squares construction from the lifted piece
            if field_action == Enums.PieceAction.LIFT and piece_color_is_consistent and self._source_square == -1:
  
                self._source_square = field_index

                self._legal_squares = list(

                    # All legal move indexes
                    map(lambda item:common.Converters.to_square_index(item, Enums.SquareType.TARGET), 
                                              
                    # All legal uci moves that start with the current square name
                    list(filter(lambda item:item[0:2]==square_name,
                                
                        # All legal uci moves
                        list(map(lambda item:str(item), self._chessboard.legal_moves))))
                    )
                )
                
                # The lifted piece can come back to its square
                self._legal_squares.append(field_index)

                        
            Log.debug(f'legalsquares:{self._legal_squares}')
            
            # We cancel the current taking back process if a second piece has been lifted
            # Otherwise we can't capture properly...
            if field_action == Enums.PieceAction.LIFT:
                self._undo_requested = False
                        
            if self._is_computer_move and field_action == Enums.PieceAction.LIFT and piece_color_is_consistent:
                # If this is a computer move then the piece lifted should equal the start of computermove
                # otherwise set legalsquares so they can just put the piece back down! If it is the correct piece then
                # adjust legalsquares so to only include the target square
                if square_name != self._computer_uci_move[0:2]:
                    # Computer move but wrong piece lifted
                    
                    if self._can_force_moves and field_index in self._legal_squares:
                        Log.info(f'Alternative computer move chosen : "{square_name}".')
                        
                    else:
                        # Wrong move - only option is to replace the piece on its square...
                        self._legal_squares = [field_index]

                else:
                    
                    if self._can_force_moves == False:
                    
                        # Forced move, correct piece lifted
                        # Only one choice possible
                        self._legal_squares = [common.Converters.to_square_index(self._computer_uci_move, Enums.SquareType.TARGET)]

            if field_action == Enums.PieceAction.PLACE and field_index not in self._legal_squares:
                
                if CentaurConfig.get_sound_settings(consts.SOUND_WRONG_MOVES):
                    CENTAUR_BOARD.beep(Enums.Sound.WRONG_MOVE)

                self._source_square = -1

                # Could be a reset request...
                self._need_starting_position_check = True

            # Taking back process
            if self._can_undo_moves and piece_color_is_consistent == False and field_action == Enums.PieceAction.LIFT:
                
                # We read the last move that has been recorded
                previous_uci_move = self.get_last_uci_move()
               
                if previous_uci_move and previous_uci_move[2:4] == square_name:
                    Log.info(f'Takeback request : "{square_name}".')
                    
                    # The only legal square is the origin from the previous move
                    self._legal_squares = [common.Converters.to_square_index(previous_uci_move, Enums.SquareType.ORIGIN)]

                    self._undo_requested = True

                    del previous_uci_move

            if field_action == Enums.PieceAction.PLACE and field_index in self._legal_squares:

                if field_index == self._source_square:
                    # Piece has simply been placed back
                    self._source_square = -1
                    self._legal_squares = []
                    
                    self._undo_requested = False
                else:
                    
                    # Previous move has been taken back
                    if self._undo_requested:
                        
                        # Undo the move
                        previous_uci_move = self._chessboard.pop().uci()
                        
                        Log.debug(f'Undoing move "{previous_uci_move}"...')

                        previous_san_move = self._san_move_list.pop()
                        
                        Log.debug(f'Move "{previous_uci_move}/{previous_san_move}" will be removed from DB...')

                        self._dal.delete_last_game_move()
                        
                        self._legal_squares = []
                        self._source_square = -1

                        if CentaurConfig.get_sound_settings(consts.SOUND_TAKEBACK_MOVES):
                            CENTAUR_BOARD.beep(Enums.Sound.TAKEBACK_MOVE)

                        CENTAUR_BOARD.led(field_index)

                        common.update_Centaur_FEN(self._chessboard.fen())

                        self.display_partial_PGN()
                        self.display_board()
                        self.update_web_ui({ 
                            "clear_board_graphic_moves":True,
                            "uci_undo_move":previous_uci_move[2:4]+previous_uci_move[:2],
                            "uci_move":self.get_last_uci_move(),
                        })
            
                        Engine.__invoke_callback(self._undo_callback_function,
                            uci_move=previous_uci_move,
                            san_move=previous_san_move,
                            field_index=field_index)
            
                        Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.PLAY)

                        self._undo_requested = False
                        self.update_evaluation()

                        del previous_uci_move
                        del previous_san_move
                        
                    else:
                        
                        Log.info(f'Piece has been moved to "{square_name}".')

                        # Piece has been moved
                        from_name = common.Converters.to_square_name(self._source_square)
                        to_name = common.Converters.to_square_name(field_index)
                        
                        def finalize_move(player_uci_move, promoted_piece = ""):
            
                            if self._is_computer_move:
                                
                                # Has the computer move been overrided?
                                if self._can_force_moves and player_uci_move != self._computer_uci_move[0:4]:
                                    
                                    # computermove is replaced since we can override it!
                                    self._computer_uci_move = player_uci_move + promoted_piece
                            
                                    Log.info(f'New computermove : "{self._computer_uci_move}".')
                                
                                uci_move = self._computer_uci_move
                            else:
                                uci_move = from_name + to_name + promoted_piece
                           
                            # Make the move
                            try:
                                move = chess.Move.from_uci(uci_move)

                                self._chessboard.push(move)
                                san_move = self.get_last_san_move()
                            except:
                                san_move = None

                            if san_move == None:
                                if CentaurConfig.get_sound_settings(consts.SOUND_WRONG_MOVES):
                                    CENTAUR_BOARD.beep(Enums.Sound.WRONG_MOVE)

                                Log.debug(f'INVALID move "{uci_move}"')

                                self._source_square = -1

                                # Could be a reset request...
                                self._need_starting_position_check = True

                            else:

                                # We invoke the client callback
                                # If the callback returns True, the move is accepted
                                if Engine.__invoke_callback(self._move_callback_function, 
                                        uci_move=uci_move,
                                        san_move=san_move,
                                        color=not self._chessboard.turn, # Move has been done, we need to reverse the color
                                        field_index=field_index):

                                    self.update_evaluation()

                                    # We record the move
                                    if self._dal.insert_new_game_move(uci_move, str(self._chessboard.fen())):
                                        Log.debug(f'Move "{uci_move}/{san_move}" has been commited.')

                                        self._legal_squares = []
                                        self._source_square = -1
                                        self._is_computer_move = False

                                        self._san_move_list.append(san_move)

                                        if CentaurConfig.get_sound_settings(consts.SOUND_CORRECT_MOVES):
                                            CENTAUR_BOARD.beep(Enums.Sound.CORRECT_MOVE)

                                        if len(self._chessboard.checkers())>0:
                                            CENTAUR_BOARD.led_array([field_index, self._chessboard.king(self._chessboard.turn)])
                                        else:
                                            CENTAUR_BOARD.led(field_index)

                                        common.update_Centaur_FEN(self._chessboard.fen())

                                        self.display_partial_PGN()
                                        self.display_board()
                                        self.update_web_ui({ 
                                            "clear_board_graphic_moves":True,
                                            "uci_move":uci_move,
                                            "san_move":san_move,
                                            "field_index":field_index })

                                        self._check_last_move_outcome_and_switch()
                                    else:
                                        Log.exception(f'Move "{uci_move}/{san_move}" HAS NOT been commited.')
                                        self.stop()

                                else:
                                    Log.debug(f'Client rejected the move "{uci_move}/{san_move}"...')

                                    # Move has been rejected by the client...
                                    self._chessboard.pop()

                        # Promotion
                        # If this is a WPAWN and squarerow is 7
                        # or a BPAWN and squarerow is 0
                        piece_name = str(self._chessboard.piece_at(self._source_square))
                        
                        if (((field_index // 8) == 7 and piece_name == "P") or ((field_index // 8) == 0 and piece_name == "p") and
                            
                            # Promotion menu display if player is human or if player overrides computer move

                            (self._is_computer_move == False or (self._is_computer_move == True and (from_name + to_name) != self._computer_uci_move[0:4]))):

                            SCREEN.draw_promotion_window()

                            def wait_for_promotion_input():

                                def _promote_key_callback(key_index):

                                    promoted_piece = ({

                                        Enums.Btn.BACK:"n", 
                                        Enums.Btn.TICK:"b", 
                                        Enums.Btn.UP:"q", 
                                        Enums.Btn.DOWN:"r", 

                                        Enums.Btn.HELP:None, 
                                        Enums.Btn.PLAY: None, 
                                        Enums.Btn.LONGPLAY: None
                                    
                                    }[key_index])

                                    if promoted_piece != None:

                                        # Back to original callbacks
                                        CENTAUR_BOARD.unsubscribe_events()

                                        self.display_board()

                                        finalize_move(from_name + to_name, promoted_piece)

                                # We temporary disable the board field callback
                                # and we add a new temporary board key callback
                                CENTAUR_BOARD.subscribe_events(_promote_key_callback, None)

                            wait_for_promotion_input()
                        else:
                            finalize_move(from_name + to_name)

        
        except Exception as e:
            Log.exception(Engine.__field_callback, e)

    def _check_last_move_outcome_and_switch(self):
        # Check the outcome
        outcome = self._chessboard.outcome(claim_draw=True)
        if outcome == None or outcome == "None" or outcome == 0:
            # Switch the turn
            Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.PLAY)
        else:
            # Depending on the outcome we can update the game information for the result
            self._dal.terminate_game(str(self._chessboard.result()))

            str_outcome = {

                    chess.Termination.CHECKMATE:"checkmate",
                    chess.Termination.STALEMATE:"stalemate",
                    chess.Termination.INSUFFICIENT_MATERIAL:"draw",
                    chess.Termination.SEVENTYFIVE_MOVES:"draw",
                    chess.Termination.FIVEFOLD_REPETITION:"draw",
                    chess.Termination.FIFTY_MOVES:"draw",
                    chess.Termination.THREEFOLD_REPETITION:"draw",
                    chess.Termination.VARIANT_WIN:"draw",
                    chess.Termination.VARIANT_LOSS:"draw",
                    chess.Termination.VARIANT_DRAW:"draw",
        
                }[outcome.termination]

            self.update_evaluation(force=True, text=str_outcome)

            self.send_to_web_clients({ 
                "turn_caption":str_outcome
            })

            Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.TERMINATION, termination=outcome.termination)

    def _evaluation_thread_instance(self):

        try:
            sf_engine = ChessEngine.get(consts.STOCKFISH_ENGINE_PATH)

            while self._thread_is_alive:

                if self._new_evaluation_requested and self._initialized:

                    self._new_evaluation_requested = False

                    if self._show_evaluation and not self._evaluation_disabled:

                        result = sf_engine.analyse(self._chessboard, chess.engine.Limit(time=1))

                        if result != None and result["score"]:

                            score = str(result["score"])

                            del result

                            Log.debug(score)

                            if "Mate" in score:
                                
                                mate = int(re.search(r'PovScore\(Mate\([-+](\d+)\)', score)[1])

                                self.update_evaluation(force=True, text=f" mate in {mate}")

                                del mate
                            else:
                                eval = score[11:24]
                                eval = eval[1:eval.find(")")]
                    
                                eval = int(eval)

                                if "BLACK" in score:
                                    eval = eval * -1

                                self.update_evaluation(force=True, value=eval)

                                del eval

                    else:
                        self.update_evaluation(force=True, disabled=True)

                time.sleep(.5)

            sf_engine.quit()

        except Exception as e:
            Log.exception(Engine._evaluation_thread_instance, e)

    def _game_thread_instance_worker(self):
        # The main thread handles the actual chess game functionality and calls back to
        # eventCallback with game events and
        # moveCallback with the actual moves made

        CENTAUR_BOARD.leds_off()
        CENTAUR_BOARD.subscribe_events(self.__key_callback, self.__field_callback)

        self._dal.delete_empty_games()

        self._chessboard = chess.Board(chess.STARTING_FEN)
        
        ticks = -1

        try:
            while self._thread_is_alive:

                # First time we are here
                # We might need to resume a game...
                if ticks == -1:

                    uci_moves_history = self._uci_moves_at_start if len(self._uci_moves_at_start)>0 else self._dal.read_uci_moves_history()

                    if len(uci_moves_history) > 0:

                        Log.info("RESUMING LAST GAME!")

                        self.__initialize()
                        
                        try:

                            last_uci_move = None

                            # We replay the previous game
                            for uci_move in uci_moves_history:

                                last_uci_move = uci_move

                                if len(uci_move)>3:
                                    move = self._chessboard.parse_uci(uci_move)
                                    san_move = self._chessboard.san(move)

                                    self._chessboard.push(move)

                                    self._san_move_list.append(san_move)
                            
                            del uci_moves_history

                            if self._chessboard.is_game_over():
                                self._need_starting_position_check = True
                                Log.info("LAST GAME WAS FINISHED!")
                            
                            else:
                                if CentaurConfig.get_sound_settings(consts.SOUND_MUSIC):
                                    CENTAUR_BOARD.beep(Enums.Sound.MUSIC)

                                common.update_Centaur_FEN(self._chessboard.fen())

                                self.display_board()
                                self.display_partial_PGN()

                                self.update_web_ui({ 
                                    "clear_board_graphic_moves":True,
                                    "uci_move":last_uci_move })

                                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.RESUME_GAME)
                                
                                self.update_evaluation()

                                self._check_last_move_outcome_and_switch()
                            
                                self._initialized = True

                        except Exception as e:
                            Log.exception(Engine._game_thread_instance_worker, e)

                # Detect if a new game has begun
                if self._need_starting_position_check:

                    if ticks < 5:
                        ticks = ticks + 1
                    else:
                        try:

                            board_state = bytearray(CENTAUR_BOARD.get_board_state())

                            # In case of full undo we do not restart a game - no need
                            if board_state == consts.BOARD_START_STATE:
                                
                                Log.info("STARTING A NEW GAME!")

                                del board_state

                                #all_objects = muppy.get_objects()
                                #global_len = len(all_objects)
                                #print(f"Global size:{global_len}")
                                #sum1 = summary.summarize(all_objects)
                                #summary.print_(sum1)

                                self._need_starting_position_check = False

                                self._chessboard = chess.Board(chess.STARTING_FEN)
                                
                                self.__initialize()
                                
                                if CentaurConfig.get_sound_settings(consts.SOUND_MUSIC):
                                    CENTAUR_BOARD.beep(Enums.Sound.MUSIC)

                                common.update_Centaur_FEN(self._chessboard.fen())
                                
                                self.display_board()
                                self.display_partial_PGN()
                                self.update_web_ui({ 
                                    "clear_board_graphic_moves":True
                                })

                                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.NEW_GAME)
                                Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.PLAY)
                                
                                self._initialized = True

                                self.update_evaluation()

                                # Log a new game in the db
                                self._dal.insert_new_game(
                                    source = self.source,
                                    event  = self._game_informations["event"],
                                    site   = self._game_informations["site"],
                                    round  = self._game_informations["round"],
                                    white  = self._game_informations["white"],
                                    black  = self._game_informations["black"]
                                )

                            ticks = 0
                        except:
                            pass

                time.sleep(.1)

        except Exception as e:
            Log.exception(Engine._game_thread_instance_worker, e)


    def initialize_web_menu(self):
        if self._socket:
            self._socket.send_message({
                "update_menu": [{
                "label":"← Back to main menu", 
                "action": { "type": "socket_sys", "value": "homescreen"}}]})
    
    def is_started(self):
        return self._started

    def start(self, uci_moves = []):

        if self._thread_is_alive:
            return

        self._uci_moves_at_start = uci_moves
        
        self._started = True

        self._need_starting_position_check = True

        self._thread_is_alive = True

        self._game_thread_instance = Thread(target=self._game_thread_instance_worker)
        self._game_thread_instance.daemon = True
        self._game_thread_instance.start()

        self._evaluation_thread_instance = Thread(target=self._evaluation_thread_instance)
        self._evaluation_thread_instance.daemon = True
        self._evaluation_thread_instance.start()

        def _on_socket_request(data, socket):

            if (self._initialized == False):
                pass

            try:
            
                response = {}

                if "pgn" in data:
                    response["pgn"] = self.get_current_pgn()
                    socket.send_message(response)

                if "fen" in data:
                    response["fen"] = self._chessboard.fen()
                    socket.send_message(response)

                if "uci_move" in data:
                    response["uci_move"] = self.get_last_uci_move()
                    socket.send_message(response)

                if "web_menu" in data:
                    self.initialize_web_menu()

                if "sys" in data:

                    if data["sys"] == "homescreen":
                        Engine.__invoke_callback(self._event_callback_function, event=Enums.Event.QUIT)
                        self.stop()

                if "standby" in data:
                    if data["standby"]:
                        SCREEN.home_screen("Game paused!")
                    else:
                        self.display_partial_PGN()
                        self.display_board()
                        self.update_web_ui({ 
                            "clear_board_graphic_moves":True,
                            "uci_move":self.get_last_uci_move(),
                        })

            except Exception as e:
                Log.exception(Engine._on_socket_request, e)
                pass

        self._socket = SocketClient.get(on_socket_request=_on_socket_request)

        self.initialize_web_menu()

        Log.info(f"{Engine.__name__} thread started.")


    def stop(self):
        # Stops the game manager
        CENTAUR_BOARD.leds_off()
        self._thread_is_alive = False

        if self._socket:
            self._socket.disconnect()

        self._game_thread_instance.join()
        self._evaluation_thread_instance.join()

        CENTAUR_BOARD.unsubscribe_events()

        Log.info(f"{Engine.__name__} thread has been stopped.")

    def cancel_evaluation(self):
        self._new_evaluation_requested = False

    def update_evaluation(self, value=None, force=False, text=None, disabled=False):
        if force:
            self._new_evaluation_requested = False
            SCREEN.draw_evaluation_bar(text=text, value=value, disabled=disabled)
        else:
            self._new_evaluation_requested = True

    def get_Stockfish_uci_move(self, _time = 1):

        try:
            sf_engine = ChessEngine.get(consts.STOCKFISH_ENGINE_PATH)
            
            moves = sf_engine.analyse(self._chessboard, chess.engine.Limit(time=_time))

            best_move = str(moves["pv"][0])
            sf_engine.quit()
            Log.info(f'Stockfish help requested :"{best_move}"')
        except:
            best_move = None

        return best_move

    def get_last_uci_move(self):
        return None if self._chessboard.ply() == 0 else self._chessboard.peek().uci()

    def get_last_san_move(self):
        try:
            move = self._chessboard.pop()
            san = self._chessboard.san(move)

            self._chessboard.push_san(san)

            return san
        except:
            return None

    def display_board(self):

        SCREEN.draw_fen(self._chessboard.fen(), startrow=1.6)

    def send_to_web_clients(self, message={}):
        # We send the message to all connected clients

        if self._evaluation_disabled:
            message["evaluation_disabled"] = True

        if self._socket:
            self._socket.send_message(message)

    def update_web_ui(self, args={}):
        # We send the new FEN to all connected clients
        if self._socket:

            message = {**{
                "pgn":self.get_current_pgn(), 
                "fen":self._chessboard.fen(),
                "uci_move":self.get_last_uci_move(),
                "checkers":list(map(lambda item:common.Converters.to_square_name(item), self._chessboard.checkers())),
                "kings":[common.Converters.to_square_name(self._chessboard.king(chess.WHITE)), common.Converters.to_square_name(self._chessboard.king(chess.BLACK))],
            }, **args}

            self._socket.send_message(message)

    def get_current_pgn(self):

        current_pgn = ""

        if len(self._san_move_list) > 0:

            # We always start to show a white move
            current_turn = chess.WHITE

            current_row_index = 1
    
            for san in self._san_move_list:

                # White move
                if current_turn == chess.WHITE:
                    if (san != None):
                        current_pgn = current_pgn + f"{current_row_index}. "+san

                # Black move
                else:
                    if san != None:
                        current_pgn = current_pgn + " "+ san + '\n'

                    current_row_index = current_row_index + 1

                # We switch the color
                current_turn = not current_turn

        return current_pgn
    
    def display_board_header(self, text):
        SCREEN.write_text(1, text, font=fonts.MEDIUM_FONT)

    def display_partial_PGN(self, row=9.3, move_count=10):

        if not self._partial_pgn_disabled:

            # Maximum displayed moves
            move_count = 10

            # We read the last san moves
            san_list = self._san_move_list[-move_count:] if self._chessboard.turn == chess.WHITE else self._san_move_list[-move_count+1:]
            san_list = list(san_list) + ([None] * move_count)
            
            # We truncate the list
            del san_list[move_count:]

            # We always start to show a white move
            current_turn = chess.WHITE
            
            current_row_move = ""
            current_row_index = int((len(self._san_move_list) -move_count +1) / 2) +1
            current_row_index = 1 if current_row_index < 1 else current_row_index

            for san in san_list:

                # White move
                if current_turn == chess.WHITE:
                    if (san == None):
                        SCREEN.write_text(row, ' '*20, centered=False)
                    else:
                        current_row_move = f"{current_row_index}. "+san
                        SCREEN.write_text(row, current_row_move, centered=False)

                # Black move
                else:
                    if san != None:
                        current_row_move = current_row_move + ".."+san
                        SCREEN.write_text(row, current_row_move, centered=False)

                    row = row + 1
                    current_row_index = current_row_index + 1

                # We switch the color
                current_turn = not current_turn

    def get_board(self):
        return self._chessboard
    
    def computer_move_available(self):
        return self._is_computer_move

    def set_computer_move(self, uci_move = None):
            
        try:

            if self._thread_is_alive == False:
                return

            if uci_move == None:
                uci_move = self._computer_uci_move

            # Set the computer move that the player is expected to make
            # in the format b2b4 , g7g8q , etc
            try:
                chess.Move.from_uci(uci_move)
            except:
                Log.debug(f'INVALID uci_computer_move:"{uci_move}"')
                return

            Log.debug(f'uci_computer_move:"{uci_move}"')

            # First set the globals so that the thread knows there is a computer move
            self._computer_uci_move = uci_move
            self._is_computer_move = True
            
            # Next indicate this on the board. First convert the text representation to the field number
            from_num = common.Converters.to_square_index(uci_move, Enums.SquareType.ORIGIN)
            to_num = common.Converters.to_square_index(uci_move, Enums.SquareType.TARGET)

            if CentaurConfig.get_sound_settings(consts.SOUND_COMPUTER_MOVES):
                CENTAUR_BOARD.beep(Enums.Sound.COMPUTER_MOVE)
   
            # Then light it up!
            CENTAUR_BOARD.led_from_to(from_num,to_num)

            self.send_to_web_clients({ 
                "clear_board_graphic_moves":False,
                "computer_uci_move":uci_move,
            })
 
        except Exception as e:
            Log.exception(Engine.set_computer_move, e)