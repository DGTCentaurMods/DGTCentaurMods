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

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import pathlib

Base = declarative_base()

class Game(Base):
    # A chess game
    __tablename__ = "game"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    created_at = Column(DateTime, server_default=func.now())
    source = Column(String(255), nullable=False) # centaur, lichess, eboard, ct800, etc
    event = Column(String(255), nullable=True)
    site = Column(String(255), nullable=True)
    round = Column(String(255), nullable=True)
    white = Column(String(255), nullable=True)
    black = Column(String(255), nullable=True)
    result = Column(String(255), nullable=True)

    def __repr__(self):
        return "<Game(id='%s', created_at='%s', source='%s')>" % (str(self.id), str(self.created_at), self.source)

class GameMove(Base):
    # A move/board state in a chess game
    __tablename__ = "gameMove"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    gameid = Column(Integer, ForeignKey("game.id"), index=True)
    move_at = Column(DateTime, server_default=func.now())
    move = Column(String(10), nullable=True)
    fen = Column(String(255), nullable=True)

    game = relationship("Game")

    def __repr__(self):
        return "<GameMove(id='%s', move_at='%s', move='%s', fen='%s')>" % (str(self.id), str(self.move_at), self.move, self.fen)

dbloc = str(pathlib.Path(__file__).parent.resolve()) + "/centaur.db"
engine = create_engine("sqlite:///" + dbloc)
Base.metadata.create_all(bind=engine)