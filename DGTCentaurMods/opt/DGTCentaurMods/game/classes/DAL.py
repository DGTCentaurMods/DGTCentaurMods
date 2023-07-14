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

from DGTCentaurMods.db import models
from DGTCentaurMods.game.classes import Log

from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session
from sqlalchemy import text

import time
import chess


class Singleton:
    __instance = None

    def __new__(cls,*args, **kwargs):
        if cls.__instance is None :
            cls.__instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls.__instance


class DAL():

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
