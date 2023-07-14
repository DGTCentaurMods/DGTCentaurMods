# This script manages a chess game, passing events and moves back to the calling script with callbacks
# The calling script is expected to manage the display itself using epaper.py
# Calling script initialises with subscribeGame(eventCallback, moveCallback, keyCallback)
# eventCallback feeds back events such as start of game, gameover
# moveCallback feeds back the chess moves made on the board
# keyCallback feeds back key presses from keys under the display

# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
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
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

# TODO

from DGTCentaurMods.board import board
from DGTCentaurMods.display import epaper
from DGTCentaurMods.db import models

from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session
from sqlalchemy import text

import threading
import time
import chess
import sys
import inspect
import os

from enum import Enum

import logging
import logging.handlers

# https://pypi.org/project/py-flags/
# pip install py-flags
from flags import Flags

from PIL import ImageFont
import pathlib

FONT_Typewriter = ImageFont.truetype(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/Typewriter Medium.ttf", 16)
FONT_Typewriter_small = ImageFont.truetype(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/Typewriter Medium.ttf", 11)

# We use the constants from board.py
# Some useful constants
#class Btn(Enum):
#    BACK = 1
#    TICK = 2
#    UP = 3
#    DOWN = 4
#    HELP = 5
#    PLAY = 6

class Event(Enum):
    NEW_GAME = 1
    RESUME_GAME = 2,
    PLAY = 3,
    REQUEST_DRAW = 4
    RESIGN_GAME = 5

class PieceAction(Enum):
    LIFT = 1
    PLACE = 2

class BoardOption(Flags):
    CAN_FORCE_MOVES = 1
    CAN_UNDO_MOVES = 2
    CAN_DO_COFFEE = 4


STARTSTATE = bytearray(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01')

HOME_DIRECTORY = os.path.expanduser( '~' )
FENLOG = HOME_DIRECTORY+"/centaur/fen.log"

class Log:

    LEVEL = logging.DEBUG

    __initialized = False

    @staticmethod
    def __init():

        try:
            LOG_DIR = HOME_DIRECTORY+"/logs"

            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)

            handler = logging.handlers.WatchedFileHandler(LOG_DIR+'/DGTCentaurMods.log')
            formatter = logging.Formatter(logging.BASIC_FORMAT)
            handler.setFormatter(formatter)
            
            root = logging.getLogger()
            root.setLevel(Log.LEVEL)
            root.addHandler(handler)

            Log.__initialized = True

            print("Logging initialized.")
            Log.info("Logging started.")

            logging.getLogger('chess.engine').setLevel(logging.INFO)

        except Exception as e:
            print(f'[Log.__init] {e}')

    @staticmethod
    def info(message):
        if Log.__initialized == False:
            Log.__init()

        logging.info(message)

    @staticmethod
    def exception(message):
        if Log.__initialized == False:
            Log.__init()

        logging.exception(message)

    @staticmethod
    def debug(message):
        if Log.__initialized == False:
            Log.__init()

        logging.debug(message)


class Converters:

    @staticmethod
    def to_square_name(square):
        square_row = (square // 8)
        square_col = (square % 8)
        square_col = 7 - square_col
        return chr(ord("a") + (7 - square_col)) + chr(ord("1") + square_row)
        
    @staticmethod
    def to_square_index(name):
        square_col = ord(name[0:1]) - ord('a')
        square_row = ord(name[1:2]) - ord('1')
        return (square_row * 8) + square_col

class Singleton:
    __instance = None

    def __new__(cls,*args, **kwargs):
        if cls.__instance is None :
            cls.__instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls.__instance


class DAL(Singleton):

    def __init__(self):

        self.__read_current_game_id()


    def __read_current_game_id(self):

        try:

            with Session(bind=models.engine) as session:

                # Get the max game id as that is this game id and fill it into game
                self._db_game_id = session.query(func.max(models.Game.id)).scalar()

            Log.debug(f"_db_game_id={self._db_game_id}")

        except Exception as e:
            Log.exception(f'[__read_current_game_id] {e}')

    def read_uci_moves_history(self):

        try:

            with Session(bind=models.engine) as session:

                # Get all the moves for the current game_id
                result = session.execute(select(models.GameMove.move).where(
                    models.GameMove.gameid == self._db_game_id).order_by(models.GameMove.id))

                result = result.scalars().all()

                Log.debug(f"read_uci_moves_history result={result}")

                return result

        except Exception as e:
            Log.exception(f'[__read_moves_history] {e}')

    def delete_empty_games(self):
        try:
            with Session(bind=models.engine) as session:

                session.execute(text("delete from gamemove where id in (select id from gamemove group by gameid having count(gameid)<2)"))
                session.commit()
                
                session.execute(text("delete from game where id in (select g.id from game g left join gamemove gm on g.id=gm.gameid group by g.id having count(g.id)<2)"))
                session.commit()

        except Exception as e:
            Log.exception(f'[delete_empty_games] {e}')

    def insert_new_game(self, source, event, site, round, white, black):

        self.delete_empty_games()

        try:

            with Session(bind=models.engine) as session:

                # Create a new game in the db
                game = models.Game(
                    source = source,
                    event  = event,
                    site   = site,
                    round  = round,
                    white  = white,
                    black  = black
                )

                session.add(game)
                
                # Now make an entry in GameMove for this start state
                game_move = models.GameMove(
                    gameid = self._db_game_id,
                    move   = '',
                    fen    = str(chess.STARTING_FEN)
                )

                session.add(game_move)
                session.commit()
                                
                self.__read_current_game_id()

        except Exception as e:
            Log.exception(f'[insert_new_game] {e}')

    def terminate_game(self, result):
        try:
            with Session(bind=models.engine) as session:
                
                game = session.query(models.Game).filter(models.Game.id == self._db_game_id).first()
                game.result = result
                session.commit()

        except Exception as e:
            Log.exception(f'[terminate_game] {e}')

    def delete_game_move(self, id):
        try:
            with Session(bind=models.engine) as session:
                stmt = delete(models.GameMove).where(models.GameMove.id == id)               
                session.execute(stmt)
                session.commit()

        except Exception as e:
            Log.exception(f'[delete_game_move] {e}')

    def insert_new_game_move(self, uci_move, fen):

        def _insert():
            with Session(bind=models.engine) as session:

                game_move = models.GameMove(
                        gameid=self._db_game_id,
                        move=uci_move,
                        fen=fen)
                        
                session.add(game_move)
                session.commit()

        # Try 5 times
        for _ in range(0, 5):
            try:
                _insert()
                e = None
            except Exception as e:
                pass

            if e:
                # Wait for one half second before trying to fetch the data again
                time.sleep(.5)  
            else:
                break

        if e:
            Log.exception(f'[insert_new_game_move] {e}')
            return False

        return True


    def read_last_db_move(self):

        # We read the last move that has been recorded
        try:

            with Session(bind=models.engine) as session:
                return session.execute(
                    select(models.GameMove)
                        .order_by(models.GameMove.id.desc())
                        .limit(1)).scalar()
    
        except Exception as e:
            Log.exception(f'[read_last_db_move] {e}')


# Game manager class
class Factory():

    _thread_is_alive = False
    _initialized = False
    _new_evaluation_requested = False

    show_evaluation = True

    def __init__(self, event_callback = None, move_callback = None, key_callback = None, flags = BoardOption.CAN_DO_COFFEE, game_informations = {}):

        epaper.writeText(3," Please place", font=FONT_Typewriter)
        epaper.writeText(4,"    pieces in", font=FONT_Typewriter)
        epaper.writeText(5,"     starting", font=FONT_Typewriter)
        epaper.writeText(6,"     position!", font=FONT_Typewriter)

        self._key_callback_function = key_callback
        self._move_callback_function = move_callback
        self._event_callback_function = event_callback

        self._game_informations = game_informations

        self.source = inspect.getsourcefile(sys._getframe(1))

        self._can_force_moves = BoardOption.CAN_FORCE_MOVES in flags
        self._can_undo_moves = BoardOption.CAN_UNDO_MOVES in flags

        board.clearSerial()


    @staticmethod
    def __invoke_callback(callback, **args):
        if callback != None:
            try:
                Log.debug(f"callback [{callback.__name__}({args})]")
                callback(args)
            except Exception as e:
                Log.exception(f"callback error:{e}")

    def __initialize(self):

        board.ledsOff()

        self._source_square = -1
        self._legal_squares = []
        self._computer_uci_move = ""
        self._is_computer_move = False
        self._db_undo_id = None
        self._san_move_list = []

        self._new_evaluation_requested = False

    def __key_callback(self, key_index):
        #key = list(filter(lambda a: a.value == key_index, Btn))[0]
        Factory.__invoke_callback(self._key_callback_function, key=key_index)

    # Receives field events from the board.
    # Positive is a field lift, negative is a field place.
    # Numbering 0 = a1, 63 = h8
    def __field_callback(self, field_index):

        if self._initialized == False:
            return

        try:
            # We do not need to check the reset if a piece is lifted
            self._need_starting_position_check = False

            current_action = PieceAction.LIFT if field_index >= 0 else PieceAction.PLACE

            field_index = abs(field_index) -1
            
            # Check the piece colour against the current turn
            piece_color_is_consistent = self._chessboard.turn == self._chessboard.color_at(field_index)
            
            square_name = Converters.to_square_name(field_index)
      
            Log.debug(f"field_index:{field_index}, square_name:{square_name}, piece_action:{current_action}")

            # Legal squares construction from the lifted piece
            if current_action == PieceAction.LIFT and piece_color_is_consistent and self._source_square == -1:
  
                self._source_square = field_index

                self._legal_squares = list(

                    # All legal move indexes
                    map(lambda item:Converters.to_square_index(item[2:4]), 
                                              
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
            if current_action == PieceAction.LIFT:
                self._db_undo_id = None
                        
            if self._is_computer_move and current_action == PieceAction.LIFT and piece_color_is_consistent:
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
                        self._legal_squares = [Converters.to_square_index(self._computer_uci_move[2:4])]

            if current_action == PieceAction.PLACE and field_index not in self._legal_squares:
                
                board.beep(board.SOUND_WRONG_MOVE)

                # Could be a reset request...
                self._need_starting_position_check = True

            # Taking back process
            if self._can_undo_moves and piece_color_is_consistent == False and current_action == PieceAction.LIFT:
                
                # We read the last move that has been recorded
                previous_db_move = self._dal.read_last_db_move()
                
                if previous_db_move.move[2:4] == square_name:
                    Log.info(f'Takeback request : "{square_name}".')
                    
                    # The only legal square is the origin from the previous move
                    self._legal_squares = [Converters.to_square_index(previous_db_move.move[0:2])]
                    
                    # We keep the DB ID of the move, in order to delete it when the piece will be placed
                    self._db_undo_id = previous_db_move.id

            if current_action == PieceAction.PLACE and field_index in self._legal_squares:

                if field_index == self._source_square:
                    # Piece has simply been placed back
                    self._source_square = -1
                    self._legal_squares = []
                    
                    self._db_undo_id = None
                else:
                    
                    # Previous move has been taken back
                    if self._db_undo_id:
                        
                        # Undo the move
                        uci_move = self._chessboard.pop()
                        
                        Log.debug(f'Undoing move "{uci_move}"...')

                        self._san_move_list.pop()
                        
                        Log.debug(f'GameMove #{self._db_undo_id} "{uci_move}" will be removed from DB...')

                        self._dal.delete_game_move(self._db_undo_id)
                        
                        self._legal_squares = []
                        self._source_square = -1
            
                        Factory.__invoke_callback(self._move_callback_function, field_index=field_index)
                        Factory.__invoke_callback(self._event_callback_function, event=Event.PLAY)

                        self._db_undo_id = None
                        self.update_evaluation()
                        
                    else:
                        
                        Log.info(f'Piece has been moved to "{square_name}".')
                    
                        # Piece has been moved
                        from_name = Converters.to_square_name(self._source_square)
                        to_name = Converters.to_square_name(field_index)
                        
                        player_uci_move = from_name + to_name
                        
                        # Promotion
                        # If this is a WPAWN and squarerow is 7
                        # or a BPAWN and squarerow is 0
                        piece_name = str(self._chessboard.piece_at(self._source_square))
                        str_promotion = ""
                        
                        if ((field_index // 8) == 7 and piece_name == "P") or ((field_index // 8) == 0 and piece_name == "p"):

                            # Promotion menu display if player is human or if player overrides computer move
                            if self._is_computer_move == False or (self._is_computer_move == True and player_uci_move != self._computer_uci_move[0:4]):
                                
                                board.promotionOptionsToBuffer(7)
                                board.displayScreenBufferPartial()
    
                                board.pauseEvents()

                                button_pressed = 0
                                while button_pressed == 0:
                                    board.sendPacket(b'\x83', b'')
                                    try:
                                        resp = board.ser.read(1000)
                                    except:
                                        
                                        if piece_name == "p":
                                            board.sendPacket(b'\x83', b'')
                                        else:
                                            board.sendPacket(b'\xb1', b'')
                                            
                                    resp = bytearray(resp)
                                    board.sendPacket(b'\x94', b'')
                                    try:
                                        resp = board.ser.read(1000)
                                    except:
                                        board.sendPacket(b'\x94', b'')
                                    resp = bytearray(resp)
                                    if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
                                        button_pressed = board.BTNBACK
                                        str_promotion = "n"
                                    if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0510000000007d17"):
                                        button_pressed = board.BTNTICK
                                        str_promotion = "b"
                                    if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0508000000007d3c"):
                                        button_pressed = board.BTNUP
                                        str_promotion = "q"
                                    if (resp.hex()[:-2] == "b10010" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a05020000000061"):
                                        button_pressed = board.BTNDOWN
                                        str_promotion = "r"

                                    time.sleep(0.1)

                                board.unPauseEvents()
                                
                        if self._is_computer_move:
                            
                            # Has the computer move been overrided?
                            if self._can_force_moves and player_uci_move != self._computer_uci_move[0:4]:
                                
                                # computermove is replaced since we can override it!
                                self._computer_uci_move = player_uci_move + str_promotion
                        
                                Log.info(f'New computermove : "{self._computer_uci_move}".')
                            
                            uci_move = self._computer_uci_move
                        else:
                            uci_move = from_name + to_name + str_promotion
                        
                        # Make the move
                        self._chessboard.push(chess.Move.from_uci(uci_move))

                        self.update_evaluation()

                        # We record the move
                        if self._dal.insert_new_game_move(uci_move, str(self._chessboard.fen())):
                            Log.debug(f'Move "{uci_move}" has been commited.')

                            self._legal_squares = []
                            self._source_square = -1
                            self._is_computer_move = False

                            self._san_move_list.append(self.get_last_san_move())

                            # We invoke the client callback
                            Factory.__invoke_callback(self._move_callback_function, uci_move=uci_move, field_index=field_index)
                            
                            # Check the outcome
                            outcome = self._chessboard.outcome(claim_draw=True)
                            if outcome == None or outcome == "None" or outcome == 0:
                                # Switch the turn
                                Factory.__invoke_callback(self._event_callback_function, event=Event.PLAY)
                            else:
                                # Depending on the outcome we can update the game information for the result
                                self._dal.terminate_game(str(self._chessboard.result()))

                                Factory.__invoke_callback(self._event_callback_function, termination=outcome.termination)
                        else:
                            Log.exception(f'Move "{uci_move}" HAS NOT been commited.')
                            self.stop()
        
        except Exception as e:
            Log.exception(f"__field_callback error:{e}")

    def _evaluation_thread_instance(self):
        try:

            _draw_evaluation = lambda disabled=False,value=0:epaper.drawEvaluationBar(row=9, value=value, disabled=disabled, font=FONT_Typewriter_small)

            sf_engine = chess.engine.SimpleEngine.popen_uci(HOME_DIRECTORY+"/centaur/engines/stockfish_pi")

            while self._thread_is_alive:

                if self._new_evaluation_requested and self._initialized:
                    if self.show_evaluation:
                        result = sf_engine.analyse(self._chessboard, chess.engine.Limit(time=1))

                        eval = int(str(result["score"].white()))

                        #epaper.writeText(14, f"Eval {eval:+}", font=FONT_Typewriter)
                        _draw_evaluation(value=eval)
                    else:
                        _draw_evaluation(disabled=True)

                    self._new_evaluation_requested = False

                time.sleep(.5)

            sf_engine.quit()
        
        except Exception as e:
            Log.exception(f"_evaluation_thread_instance error:{e}")
        

    def _game_thread_instance(self):
        # The main thread handles the actual chess game functionality and calls back to
        # eventCallback with game events and
        # moveCallback with the actual moves made

        board.ledsOff()
        board.subscribeEvents(self.__key_callback, self.__field_callback)

        self._dal = DAL()

        self._dal.delete_empty_games()

        self._chessboard = chess.Board(chess.STARTING_FEN)

        ticks = -1

        try:
            while self._thread_is_alive:

                # First time we are here
                # We might need to resume a game...
                if ticks == -1:

                    all_uci_moves = self._dal.read_uci_moves_history()

                    if len(all_uci_moves) > 0:

                        Log.info("RESUMING LAST GAME!")

                        self.__initialize()
                        
                        try:

                            # We replay the previous game
                            for uci_move in all_uci_moves:

                                if len(uci_move)>3:
                                    move = self._chessboard.parse_uci(uci_move)
                                    san_move = self._chessboard.san(move)

                                    self._chessboard.push(move)

                                    self._san_move_list.append(san_move)
                            
                            board.beep(board.SOUND_GENERAL)

                            Factory.__invoke_callback(self._event_callback_function, event=Event.RESUME_GAME)
                            Factory.__invoke_callback(self._move_callback_function)
                            Factory.__invoke_callback(self._event_callback_function, event=Event.PLAY)
                        
                            self._initialized = True

                            self.update_evaluation()

                        except Exception as e:
                            Log.exception(f"__game_thread error (while resuming game):{e}")

                # Detect if a new game has begun
                if self._need_starting_position_check:
                    if ticks < 5:
                        ticks = ticks + 1
                    else:
                        try:
                            board.pauseEvents()
                            cs = board.getBoardState()
                            board.unPauseEvents()

                            # In case of full undo we do not restart a game - no need
                            if bytearray(cs) == STARTSTATE:
                                
                                Log.info("STARTING A NEW GAME!")

                                self._chessboard = chess.Board(chess.STARTING_FEN)

                                self.__initialize()
    
                                self._need_starting_position_check = False
                                
                                board.beep(board.SOUND_GENERAL)

                                Factory.__invoke_callback(self._event_callback_function, event=Event.NEW_GAME)
                                Factory.__invoke_callback(self._move_callback_function)
                                Factory.__invoke_callback(self._event_callback_function, event=Event.PLAY)
                                
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

                time.sleep(0.1)
        
        except Exception as e:
            Log.exception(f"__game_thread error:{e}")

    
    def start(self):

        if self._thread_is_alive:
            return

        self._need_starting_position_check = True

        self._thread_is_alive = True

        self._game_thread_instance = threading.Thread(target=self._game_thread_instance)
        self._game_thread_instance.daemon = True
        self._game_thread_instance.start()

        self._evaluation_thread_instance = threading.Thread(target=self._evaluation_thread_instance)
        self._evaluation_thread_instance.daemon = True
        self._evaluation_thread_instance.start()

        Log.debug("_game_thread_instance started.")


    def stop(self):
        # Stops the game manager
        board.ledsOff()
        self._thread_is_alive = False

        self._game_thread_instance.join()
        self._evaluation_thread_instance.join()

        Log.debug("_game_thread_instance has been stopped.")

    def update_evaluation(self):
        self._new_evaluation_requested = True

    def get_Stockfish_uci_move(self, _time = 1):
        sf_engine = chess.engine.SimpleEngine.popen_uci(HOME_DIRECTORY+"/centaur/engines/stockfish_pi")
        moves = sf_engine.analyse(self._chessboard, chess.engine.Limit(time=_time))

        best_move = str(moves["pv"][0])
        sf_engine.quit()

        Log.info(f'Stockfish help requested :"{best_move}"')

        return best_move
    
    def get_Stockfish_evaluation(self):
        sf_engine = chess.engine.SimpleEngine.popen_uci(HOME_DIRECTORY+"/centaur/engines/stockfish_pi")
        moves = sf_engine.analyse(self._chessboard, chess.engine.Limit(time=_time))

        best_move = str(moves["pv"][0])
        sf_engine.quit()

        Log.info(f'Stockfish help requested :"{best_move}"')

        return best_move

    def get_last_san_move(self):
        move = self._chessboard.pop()
        san = self._chessboard.san(move)

        self._chessboard.push_san(san)

        return san
    
    def load_Centaur_FEN(self):

        Log.debug("Loading Centaur FEN...")

        f = open(FENLOG, "r")
        fen = f.readline()
        f.close()

        self._chessboard = chess.Board(fen)

    def update_Centaur_FEN(self):
        f = open(FENLOG, "w")
        f.write(self._chessboard.fen())
        f.close()

    def display_board(self):
        epaper.drawFen(self._chessboard.fen())

    def display_current_PGN(self, row=10, move_count=10):

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
                    epaper.writeText(row, ' '*20, font=FONT_Typewriter)
                else:
                    current_row_move = f"{current_row_index}. "+san
                    epaper.writeText(row, current_row_move, font=FONT_Typewriter)

            # Black move
            else:
                if san != None:
                    current_row_move = current_row_move + ".."+san
                    epaper.writeText(row, current_row_move, font=FONT_Typewriter)

                row = row + 1
                current_row_index = current_row_index + 1

            # We switch the color
            current_turn = not current_turn

    """""
    def resignGame(sideresigning):
        # Take care of updating the data for a resigned game and callback to the program with the
        # winner. sideresigning = 1 for white, 2 for black
        resultstr = ""
        if sideresigning == 1:
            resultstr = "0-1"
        else:
            resultstr = "1-0"
        tg = session.query(models.Game).filter(models.Game.id == db_game_id).first()
        tg.result = resultstr
        session.flush()
        session.commit()
        event_callback_function("Termination.RESIGN")
        
    def getResult():
        # Looks up the result of the last game and returns it
        gamedata = session.execute(
            select(models.Game.created_at, models.Game.source, models.Game.event, models.Game.site, models.Game.round,
            models.Game.white, models.Game.black, models.Game.result, models.Game.id).
            order_by(models.Game.id.desc())
        ).first()
        return str(gamedata["result"])

    def drawGame():
        # Take care of updating the data for a drawn game
        tg = session.query(models.Game).filter(models.Game.id == db_game_id).first()
        tg.result = "1/2-1/2"
        session.flush()
        session.commit()
        event_callback_function("Termination.DRAW")
    """""

    def get_board(self):
        return self._chessboard

    def set_computer_move(self, uci_move):
            
        try:
            Log.debug(f"uci_computer_move:{uci_move}")

            # We don't care about the computer move if a new game started
            # TODO might not work when computer plays white
            #if (self.new_game == 1):
            #    return

            # Set the computer move that the player is expected to make
            # in the format b2b4 , g7g8q , etc
            if len(uci_move) < 4:
                return
            
            # First set the globals so that the thread knows there is a computer move
            self._computer_uci_move = uci_move
            self._is_computer_move = True
            
            # Next indicate this on the board. First convert the text representation to the field number
            from_num = Converters.to_square_index(uci_move[0:2])
            to_num = Converters.to_square_index(uci_move[2:4])

            # Then light it up!
            board.ledFromTo(from_num,to_num)
 
        except Exception as e:
            Log.exception(f"computer_move error:{e}")

"""""
def clockThread():
    # This thread just decrements the clock and updates the epaper
    global whitetime
    global blacktime
    global current_turn
    global kill
    global chessboard
    while kill == 0:
        time.sleep(2) # epaper refresh rate means we can only have an accuracy of around 2 seconds :(
        if whitetime > 0 and current_turn == 1 and chessboard.fen() != chess.STARTING_FEN:
            whitetime = whitetime - 2
        if blacktime > 0 and current_turn == 0:
            blacktime = blacktime - 2
        wmin = whitetime // 60
        wsec = whitetime % 60
        bmin = blacktime // 60
        bsec = blacktime % 60
        timestr = "{:02d}".format(wmin) + ":" + "{:02d}".format(wsec) + "       " + "{:02d}".format(
            bmin) + ":" + "{:02d}".format(bsec)
        epaper.writeText(13, timestr)

whitetime = 0
blacktime = 0
def setClock(white,black):
    # Set the clock
    global whitetime
    global blacktime
    whitetime = white
    blacktime = black

def startClock():
    # Start the clock. It writes to line 13
    wmin = whitetime // 60
    wsec = whitetime % 60
    bmin = blacktime // 60
    bsec = blacktime % 60
    timestr = "{:02d}".format(wmin) + ":" + "{:02d}".format(wsec) + "       " + "{:02d}".format(bmin) + ":" + "{:02d}".format(bsec)
    epaper.writeText(13,timestr)
    clockthread = threading.Thread(target=clockThread, args=())
    clockthread.daemon = True
    clockthread.start()
"""""
