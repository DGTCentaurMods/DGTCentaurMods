# This script manages a chess game, passing events and moves back to the calling script with callbacks
# The calling script is expected to manage the display itself using epaper.py
# Calling script initialises with subscribeGame(eventCallback, moveCallback, keyCallback)
# eventCallback feeds back events such as start of game, gameover
# moveCallback feeds back the chess moves made on the board
# keyCallback feeds back key presses from keys under the display

# TODO

from DGTCentaurMods.board import boardfunctions
from DGTCentaurMods.display import epaper
from DGTCentaurMods.db import models
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, func
import threading
import time
import chess
import sys
import inspect

# Some useful constants
BTNBACK = 1
BTNTICK = 2
BTNUP = 3
BTNDOWN = 4
BTNHELP = 5
BTNPLAY = 6
EVENT_NEW_GAME = 1
EVENT_BLACK_TURN = 2
EVENT_WHITE_TURN = 3

kill = 0
startstate = bytearray(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01')
newgame = 0
keycallbackfunction = None
movecallbackfunction = None
eventcallbackfunction = None
board = chess.Board()
curturn = 1
sourcesq = -1
legalsquares = []
pausekeys = 0
computermove = ""
forcemove = 0
source = ""
gamedbid = -1
session = None

gameinfo_event = ""
gameinfo_site = ""
gameinfo_round = ""
gameinfo_white = ""
gameinfo_black = ""

def keycallback(keypressed):
    # Receives the key pressed and passes back to the script calling game manager
    global keycallbackfunction
    if keycallbackfunction != None:
        keycallbackfunction(keypressed)

def fieldcallback(field):
    # Receives field events. Positive is a field lift, negative is a field place. Numbering 0 = a1, 63 = h8
    # Use this to calculate moves
    global board
    global curturn
    global movecallbackfunction
    global sourcesq
    global legalsquares
    global eventcallbackfunction
    global newgame
    global keycallback
    global pausekeys
    global computermove
    global forcemove
    global source
    global gamedbid
    global session
    lift = 0
    place = 0
    if field >= 0:
        lift = 1
    else:
        place = 1
        field = field * -1
    field = field - 1
    # Check the piece colour against the current turn
    pc = board.color_at(field)
    vpiece = 0
    if curturn == 0 and pc == False:
        vpiece = 1
    if curturn == 1 and pc == True:
        vpiece = 1
    squarerow = (field // 8)
    squarecol = (field % 8)
    squarecol = 7 - squarecol
    fieldname = chr(ord("a") + (7 - squarecol)) + chr(ord("1") + squarerow)
    legalmoves = board.legal_moves
    lmoves = list(legalmoves)
    if lift == 1 and field not in legalsquares and sourcesq < 0 and vpiece == 1:
        # Generate a list of places this piece can move to
        lifted = 1
        legalsquares = []
        legalsquares.append(field)
        sourcesq = field
        for x in range(0, 64):
            sqxr = (x // 8)
            sqxc = (x % 8)
            sqxc = 7 - sqxc
            fx = chr(ord("a") + (7 - sqxc)) + chr(ord("1") + sqxr)
            tm = fieldname + fx
            found = 0
            try:
                for q in range(0,len(lmoves)):
                    if str(tm[0:4]) == str(lmoves[q])[0:4]:
                        found = 1
                        break
            except:
                pass
            if found == 1:
                legalsquares.append(x)
    if forcemove == 1 and lift == 1 and vpiece == 1:
        # If this is a forced move (computer move) then the piece lifted should equal the start of computermove
        # otherwise set legalsquares so they can just put the piece back down! If it is the correct piece then
        # adjust legalsquares so to only include the target square
        if fieldname != computermove[0:2]:
            # Forced move but wrong piece lifted
            legalsquares = []
            legalsquares.append(field)
        else:
            # Forced move, correct piece lifted, limit legal squares
            target = computermove[2:4]
            # Convert the text in target to the field number
            sqcol = ord(target[0:1]) - ord('a')
            sqrow = ord(target[1:2]) - ord('1')
            tsq = (sqrow * 8) + (sqcol)
            legalsquares = []
            legalsquares.append(tsq)
    if place == 1 and field not in legalsquares:
        boardfunctions.beep(boardfunctions.SOUND_WRONG_MOVE)
    if place == 1 and field in legalsquares:
        newgame = 0
        if field == sourcesq:
            # Piece has simply been placed back
            sourcesq = -1
            legalsquares = []
        else:
            # Piece has been moved
            squarerow = (sourcesq // 8)
            squarecol = (sourcesq % 8)
            squarecol = 7 - squarecol
            fromname = chr(ord("a") + (7 - squarecol)) + chr(ord("1") + squarerow)
            squarerow = (field // 8)
            squarecol = (field % 8)
            squarecol = 7 - squarecol
            toname = chr(ord("a") + (7 - squarecol)) + chr(ord("1") + squarerow)
            # Promotion
            # If this is a WPAWN and squarerow is 7
            # or a BPAWN and squarerow is 0
            pname = str(board.piece_at(sourcesq))
            pr = ""
            if (field // 8) == 7 and pname == "P":
                screenback = epaper.epaperbuffer.copy()
                tosend = bytearray(b'\xb1\x00\x08\x06\x50\x50\x08\x00\x08\x59\x08\x00');
                tosend[2] = len(tosend)
                tosend[len(tosend) - 1] = boardfunctions.checksum(tosend)
                boardfunctions.ser.write(tosend)
                epaper.promotionOptions(13)
                pausekeys = 1
                time.sleep(1)
                buttonPress = 0
                while buttonPress == 0:
                    boardfunctions.ser.read(1000000)
                    tosend = bytearray(b'\x83\x06\x50\x59')
                    boardfunctions.ser.write(tosend)
                    resp = boardfunctions.ser.read(10000)
                    resp = bytearray(resp)
                    tosend = bytearray(b'\x94\x06\x50\x6a')
                    boardfunctions.ser.write(tosend)
                    expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
                    resp = boardfunctions.ser.read(10000)
                    resp = bytearray(resp)
                    if (resp.hex() == "b10011065000140a0501000000007d4700"):
                        buttonPress = 1  # BACK
                        pr = "n"
                    if (resp.hex() == "b10011065000140a0510000000007d175f"):
                        buttonPress = 2  # TICK
                        pr = "b"
                    if (resp.hex() == "b10011065000140a0508000000007d3c7c"):
                        buttonPress = 3  # UP
                        pr = "q"
                    if (resp.hex() == "b10010065000140a050200000000611d"):
                        buttonPress = 4  # DOWN
                        pr = "r"
                    time.sleep(0.1)
                epaper.epaperbuffer = screenback.copy()
                pausekeys = 2
            if (field // 8) == 0 and pname == "p":
                screenback = epaper.epaperbuffer.copy()
                tosend = bytearray(b'\xb1\x00\x08\x06\x50\x50\x08\x00\x08\x59\x08\x00');
                tosend[2] = len(tosend)
                tosend[len(tosend) - 1] = boardfunctions.checksum(tosend)
                boardfunctions.ser.write(tosend)
                if forcemove == 0:
                    epaper.promotionOptions(13)
                    pausekeys = 1
                    time.sleep(1)
                    buttonPress = 0
                    while buttonPress == 0:
                        boardfunctions.ser.read(1000000)
                        tosend = bytearray(b'\x83\x06\x50\x59')
                        boardfunctions.ser.write(tosend)
                        resp = boardfunctions.ser.read(10000)
                        resp = bytearray(resp)
                        tosend = bytearray(b'\x94\x06\x50\x6a')
                        boardfunctions.ser.write(tosend)
                        expect = bytearray(b'\xb1\x00\x06\x06\x50\x0d')
                        resp = boardfunctions.ser.read(10000)
                        resp = bytearray(resp)
                        if (resp.hex() == "b10011065000140a0501000000007d4700"):
                            buttonPress = 1  # BACK
                            pr = "n"
                        if (resp.hex() == "b10011065000140a0510000000007d175f"):
                            buttonPress = 2  # TICK
                            pr = "b"
                        if (resp.hex() == "b10011065000140a0508000000007d3c7c"):
                            buttonPress = 3  # UP
                            pr = "q"
                        if (resp.hex() == "b10010065000140a050200000000611d"):
                            buttonPress = 4  # DOWN
                            pr = "r"
                        time.sleep(0.1)
                    epaper.epaperbuffer = screenback.copy()
                    pausekeys = 2
            if forcemove == 1:
                mv = computermove
            mv = fromname + toname + pr
            # Make the move and update fen.log
            board.push(chess.Move.from_uci(mv))
            fenlog = "/home/pi/centaur/fen.log"
            f = open(fenlog, "w")
            f.write(board.fen())
            f.close()
            gamemove = models.GameMove(
                gameid=gamedbid,
                move=mv,
                fen=str(board.fen())
            )
            session.add(gamemove)
            session.commit()
            legalsquares = []
            sourcesq = -1
            boardfunctions.ledsOff()
            forcemove = 0
            if movecallbackfunction != None:
                movecallbackfunction(mv)
            boardfunctions.beep(boardfunctions.SOUND_GENERAL)
            # Check the outcome
            print("check outcome")
            outc = board.outcome(claim_draw=True)
            print(outc)
            if outc == None or outc == "None" or outc == 0:
                # Switch the turn
                if curturn == 0:
                    curturn = 1
                    if eventcallbackfunction != None:
                        eventcallbackfunction(EVENT_WHITE_TURN)
                else:
                    curturn = 0
                    if eventcallbackfunction != None:
                        eventcallbackfunction(EVENT_BLACK_TURN)
            else:
                tosend = bytearray(b'\xb1\x00\x08\x06\x50\x50\x08\x00\x08\x59\x08\x00');
                tosend[2] = len(tosend)
                tosend[len(tosend) - 1] = boardfunctions.checksum(tosend)
                boardfunctions.ser.write(tosend)
                # Depending on the outcome we can update the game information for the result
                resultstr = str(board.result())
                tg = session.query(models.Game).filter(models.Game.id == gamedbid).first()
                tg.result = resultstr
                session.flush()
                session.commit()
                eventcallbackfunction(str(outc.termination))


def gameThread(eventCallback, moveCallback, keycallback):
    # The main thread handles the actual chess game functionality and calls back to
    # eventCallback with game events and
    # moveCallback with the actual moves made
    global kill
    global startstate
    global newgame
    global board
    global curturn
    global keycallbackfunction
    global movecallbackfunction
    global eventcallbackfunction
    global pausekeys
    global source
    global gamedbid
    global session
    global gameinfo_event
    global gameinfo_site
    global gameinfo_round
    global gameinfo_white
    global gameinfo_black
    keycallbackfunction = keycallback
    movecallbackfunction = moveCallback
    eventcallbackfunction = eventCallback
    boardfunctions.ledsOff()
    boardfunctions.subscribeEvents(keycallback, fieldcallback)
    t = 0
    pausekeys = 0
    while kill == 0:
        # Detect if a new game has begun
        if newgame == 0:
            if t < 5:
                t = t + 1
            else:
                try:
                    boardfunctions.pauseEvents()
                    cs = boardfunctions.getBoardState()
                    boardfunctions.unPauseEvents()
                    if bytearray(cs) == startstate:
                        eventCallback(EVENT_NEW_GAME)
                        eventCallback(EVENT_WHITE_TURN)
                        newgame = 1
                        curturn = 1
                        board = chess.Board()
                        fenlog = "/home/pi/centaur/fen.log"
                        f = open(fenlog, "w")
                        f.write(board.fen())
                        f.close()
                        boardfunctions.beep(boardfunctions.SOUND_GENERAL)
                        time.sleep(0.3)
                        boardfunctions.beep(boardfunctions.SOUND_GENERAL)
                        # Log a new game in the db
                        game = models.Game(
                            source=source,
                            event=gameinfo_event,
                            site=gameinfo_site,
                            round=gameinfo_round,
                            white=gameinfo_white,
                            black=gameinfo_black
                        )
                        print(game)
                        session.add(game)
                        session.commit()
                        # Get the max game id as that is this game id and fill it into gamedbid
                        gamedbid = session.query(func.max(models.Game.id)).scalar()
                        # Now make an entry in GameMove for this start state
                        gamemove = models.GameMove(
                            gameid = gamedbid,
                            move = '',
                            fen = str(board.fen())
                        )
                        session.add(gamemove)
                        session.commit()
                    t = 0
                except:
                    pass
        if pausekeys == 1:
            boardfunctions.pauseEvents()
        if pausekeys == 2:
            boardfunctions.unPauseEvents()
            pausekeys = 0
        time.sleep(0.1)

def computerMove(mv):
    # Set the computer move that the player is expected to make
    # in the format b2b4 , g7g8q , etc
    global computermove
    global forcemove
    if len(mv) < 4:
        return
    # First set the globals so that the thread knows there is a computer move
    computermove = mv
    forcemove = 1
    # Next indicate this on the board. First convert the text representation to the field number
    fromnum = ((ord(mv[1:2]) - ord("1")) * 8) + (ord(mv[0:1]) - ord("a"))
    tonum = ((ord(mv[3:4]) - ord("1")) * 8) + (ord(mv[2:3]) - ord("a"))
    # Then light it up!
    boardfunctions.ledFromTo(fromnum,tonum)

def setGameInfo(gi_event,gi_site,gi_round,gi_white,gi_black):
    # Call before subscribing if you want to set further information about the game for the PGN files
    global gameinfo_event
    global gameinfo_site
    global gameinfo_round
    global gameinfo_white
    global gameinfo_black
    gameinfo_event = gi_event
    gameinfo_site = gi_site
    gameinfo_round = gi_round
    gameinfo_white = gi_white
    gameinfo_black = gi_black

def subscribeGame(eventCallback, moveCallback, keyCallback):
    # Subscribe to the game manager
    global source
    global gamedbid
    global session
    source = inspect.getsourcefile(sys._getframe(1))
    Session = sessionmaker(bind=models.engine)
    session = Session()

    boardfunctions.clearSerial()
    gamethread = threading.Thread(target=gameThread, args=([eventCallback, moveCallback, keyCallback]))
    gamethread.daemon = True
    gamethread.start()

def unsubscribeGame():
    # Stops the game manager
    global kill
    kill = 1