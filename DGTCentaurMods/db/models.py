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