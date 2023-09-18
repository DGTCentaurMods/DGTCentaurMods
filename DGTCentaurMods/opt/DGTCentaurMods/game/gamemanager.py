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

from DGTCentaurMods.board import *
from DGTCentaurMods.display import epaper
from DGTCentaurMods.db import models
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, func, select
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
EVENT_REQUEST_DRAW = 4
EVENT_RESIGN_GAME = 5

kill = 0
startstate = bytearray(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01')
newgame = 0
keycallbackfunction = None
movecallbackfunction = None
eventcallbackfunction = None
takebackcallbackfunction = None
cboard = chess.Board()
curturn = 1
sourcesq = -1
legalsquares = []
pausekeys = 0
computermove = ""
forcemove = 0
source = ""
gamedbid = -1
session = None
showingpromotion = False

gameinfo_event = ""
gameinfo_site = ""
gameinfo_round = ""
gameinfo_white = ""
gameinfo_black = ""

inmenu = 0

boardstates = []

def collectBoardState():
    # Append the board state to boardstates
    global boardstates
    boardstates.append(board.getBoardState())    

def checkLastBoardState():
    # If the current board state is the state of the board from the move before
    # then a takeback is in progress
    global boardstates
    global gamebid
    global session
    global cboard
    global takebackcallbackfunction
    global curturn
    if takebackcallbackfunction != None:
        c = board.getBoardState()
        if c == boardstates[len(boardstates) - 2]:    
            board.ledsOff()            
            boardstates = boardstates[:-1] 
            # For a takeback we need to remove the last move logged to the database,
            # update the fen. Switch the turn and alert the calling script of a takeback
            lastmovemade = session.query(models.GameMove).order_by(models.GameMove.id.desc()).first()
            session.delete(lastmovemade)
            session.commit()
            cboard.pop()
            fenlog = "/home/pi/centaur/fen.log"
            f = open(fenlog, "w")
            f.write(cboard.fen())
            f.close()            
            if curturn == 0:
                curturn = 1
            else:
                curturn = 0
            board.beep(board.SOUND_GENERAL)
            takebackcallbackfunction()
            return True    
    return False    

def keycallback(keypressed):
    # Receives the key pressed and passes back to the script calling game manager
    # Here we make an exception though and takeover control of the ? key. We can use this
    # key to present a menu for draw offers or resigning.
    global keycallbackfunction
    global eventcallbackfunction
    global inmenu
    if keycallbackfunction != None:
        if inmenu == 0 and keypressed != BTNHELP:
            keycallbackfunction(keypressed)
        if inmenu == 0 and keypressed == BTNHELP:
            # If we're not already in the menu and the user presses the question mark
            # key then let's bring up the menu
            inmenu = 1
            epaper.resignDrawMenu(14)
        if inmenu == 1 and keypressed == BTNBACK:
            epaper.writeText(14,"                   ")
        if inmenu == 1 and keypressed == BTNUP:
            epaper.writeText(14,"                   ")
            eventcallbackfunction(EVENT_REQUEST_DRAW)
            inmenu = 0
        if inmenu == 1 and keypressed == BTNDOWN:
            epaper.writeText(14,"                   ")
            eventcallbackfunction(EVENT_RESIGN_GAME)
            inmenu = 0

def fieldcallback(field):
    # Receives field events. Positive is a field lift, negative is a field place. Numbering 0 = a1, 63 = h8
    # Use this to calculate moves
    global cboard
    global curturn
    global movecallbackfunction
    global sourcesq
    global legalsquares
    global eventcallbackfunction
    global newgame
    global pausekeys
    global computermove
    global forcemove
    global source
    global gamedbid
    global session
    global showingpromotion
    lift = 0
    place = 0
    if field >= 0:
        lift = 1
    else:
        place = 1
        field = field * -1
    field = field - 1
    # Check the piece colour against the current turn
    pc = cboard.color_at(field)
    vpiece = 0
    if curturn == 0 and pc == False:
        vpiece = 1
    if curturn == 1 and pc == True:
        vpiece = 1
    squarerow = (field // 8)
    squarecol = (field % 8)
    squarecol = 7 - squarecol
    fieldname = chr(ord("a") + (7 - squarecol)) + chr(ord("1") + squarerow)
    legalmoves = cboard.legal_moves
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
        board.beep(board.SOUND_WRONG_MOVE)
        checkLastBoardState()
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
            pname = str(cboard.piece_at(sourcesq))
            pr = ""
            if (field // 8) == 7 and pname == "P":
                screenback = epaper.epaperbuffer.copy()
                #Beep
                tosend = bytearray(b'\xb1\x00\x08' + board.addr1.to_bytes(1, byteorder='big') + board.addr2.to_bytes(1, byteorder='big') + b'\x50\x08\x00\x08\x59\x08\x00')
                tosend[2] = len(tosend)
                tosend[len(tosend) - 1] = board.checksum(tosend)
                board.ser.write(tosend)
                if forcemove == 0:
                    showingpromotion = True
                    epaper.promotionOptions(13)
                    pausekeys = 1
                    time.sleep(1)
                    buttonPress = 0
                    while buttonPress == 0:
                        board.sendPacket(b'\x83', b'')
                        try:
                            resp = board.ser.read(1000)
                        except:
                            board.sendPacket(b'\xb1', b'')
                        resp = bytearray(resp)
                        board.sendPacket(b'\x94', b'')
                        try:
                            resp = board.ser.read(1000)
                        except:
                            board.sendPacket(b'\x94', b'')
                        resp = bytearray(resp)
                        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
                            buttonPress = 1  # BACK
                            pr = "n"
                        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0510000000007d17"):
                            buttonPress = 2  # TICK
                            pr = "b"
                        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0508000000007d3c"):
                            buttonPress = 3  # UP
                            pr = "q"
                        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a05020000000061"):
                            buttonPress = 4  # DOWN
                            pr = "r"
                        time.sleep(0.1)
                    epaper.epaperbuffer = screenback.copy()
                    showingpromotion = False
                    pausekeys = 2
            if (field // 8) == 0 and pname == "p":
                screenback = epaper.epaperbuffer.copy()
                #Beep
                tosend = bytearray(b'\xb1\x00\x08' + board.addr1.to_bytes(1, byteorder='big') + board.addr2.to_bytes(1, byteorder='big') + b'\x50\x08\x00\x08\x59\x08\x00')
                tosend[2] = len(tosend)
                tosend[len(tosend) - 1] = board.checksum(tosend)
                board.ser.write(tosend)
                if forcemove == 0:
                    showingpromotion = True
                    epaper.promotionOptions(13)
                    pausekeys = 1
                    time.sleep(1)
                    buttonPress = 0
                    while buttonPress == 0:
                        board.sendPacket(b'\x83', b'')
                        try:
                            resp = board.ser.read(1000)
                        except:
                            board.sendPacket(b'\x83', b'')
                        resp = bytearray(resp)
                        board.sendPacket(b'\x94', b'')
                        try:
                            resp = board.ser.read(1000)
                        except:
                            board.sendPacket(b'\x94', b'')
                        resp = bytearray(resp)
                        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
                            buttonPress = 1  # BACK
                            pr = "n"
                        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0510000000007d17"):
                            buttonPress = 2  # TICK
                            pr = "b"
                        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0508000000007d3c"):
                            buttonPress = 3  # UP
                            pr = "q"
                        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a05020000000061"):
                            buttonPress = 4  # DOWN
                            pr = "r"
                        time.sleep(0.1)
                    showingpromotion = False
                    epaper.epaperbuffer = screenback.copy()
                    pausekeys = 2
                    
            if forcemove == 1:
                mv = computermove
            else:
                mv = fromname + toname + pr
            # Make the move and update fen.log
            cboard.push(chess.Move.from_uci(mv))
            fenlog = "/home/pi/centaur/fen.log"
            f = open(fenlog, "w")
            f.write(cboard.fen())
            f.close()
            gamemove = models.GameMove(
                gameid=gamedbid,
                move=mv,
                fen=str(cboard.fen())
            )
            session.add(gamemove)
            session.commit()
            collectBoardState()
            legalsquares = []
            sourcesq = -1
            board.ledsOff()
            forcemove = 0
            if movecallbackfunction != None:
                movecallbackfunction(mv)
            board.beep(board.SOUND_GENERAL)
            # Also light up the square moved to
            board.led(field)
            # Check the outcome
            outc = cboard.outcome(claim_draw=True)
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
                tosend = bytearray(b'\xb1\x00\x08' + board.addr1.to_bytes(1, byteorder='big') + board.addr2.to_bytes(1, byteorder='big') + b'\x50\x08\x00\x08\x59\x08\x00');
                tosend[2] = len(tosend)
                tosend[len(tosend) - 1] = board.checksum(tosend)
                board.ser.write(tosend)
                # Depending on the outcome we can update the game information for the result
                resultstr = str(cboard.result())
                tg = session.query(models.Game).filter(models.Game.id == gamedbid).first()
                tg.result = resultstr
                session.flush()
                session.commit()
                eventcallbackfunction(str(outc.termination))

def resignGame(sideresigning):
    # Take care of updating the data for a resigned game and callback to the program with the
    # winner. sideresigning = 1 for white, 2 for black
    resultstr = ""
    if sideresigning == 1:
        resultstr = "0-1"
    else:
        resultstr = "1-0"
    tg = session.query(models.Game).filter(models.Game.id == gamedbid).first()
    tg.result = resultstr
    session.flush()
    session.commit()
    eventcallbackfunction("Termination.RESIGN")
    
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
    tg = session.query(models.Game).filter(models.Game.id == gamedbid).first()
    tg.result = "1/2-1/2"
    session.flush()
    session.commit()
    eventcallbackfunction("Termination.DRAW")

def gameThread(eventCallback, moveCallback, keycallbacki, takebackcallbacki):
    # The main thread handles the actual chess game functionality and calls back to
    # eventCallback with game events and
    # moveCallback with the actual moves made
    global kill
    global startstate
    global newgame
    global cboard
    global curturn
    global keycallbackfunction
    global movecallbackfunction
    global eventcallbackfunction
    global takebackcallbackfunction
    global pausekeys
    global source
    global gamedbid
    global session
    global gameinfo_event
    global gameinfo_site
    global gameinfo_round
    global gameinfo_white
    global gameinfo_black
    keycallbackfunction = keycallbacki
    movecallbackfunction = moveCallback
    eventcallbackfunction = eventCallback
    takebackcallbackfunction = takebackcallbacki
    board.ledsOff()
    board.subscribeEvents(keycallback, fieldcallback)
    t = 0
    pausekeys = 0
    while kill == 0:
        # Detect if a new game has begun
        if newgame == 0:
            if t < 5:
                t = t + 1
            else:
                try:
                    board.pauseEvents()
                    cs = board.getBoardState()
                    board.unPauseEvents()
                    if bytearray(cs) == startstate:
                        newgame = 1
                        curturn = 1
                        cboard = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
                        fenlog = "/home/pi/centaur/fen.log"
                        f = open(fenlog, "w")
                        f.write(cboard.fen())
                        f.close()
                        board.beep(board.SOUND_GENERAL)
                        time.sleep(0.3)
                        board.beep(board.SOUND_GENERAL)
                        board.ledsOff()
                        eventCallback(EVENT_NEW_GAME)
                        eventCallback(EVENT_WHITE_TURN)
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
                            fen = str(cboard.fen())
                        )
                        session.add(gamemove)
                        session.commit()
                        boardstates = []
                        collectBoardState()
                    t = 0
                except:
                    pass
        if pausekeys == 1:
            board.pauseEvents()
        if pausekeys == 2:
            board.unPauseEvents()
            pausekeys = 0
        time.sleep(0.1)

def clockThread():
    # This thread just decrements the clock and updates the epaper
    global whitetime
    global blacktime
    global curturn
    global kill
    global cboard
    global showingpromotion
    while kill == 0:
        time.sleep(2) # epaper refresh rate means we can only have an accuracy of around 2 seconds :(
        if whitetime > 0 and curturn == 1 and cboard.fen() != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
            whitetime = whitetime - 2
        if blacktime > 0 and curturn == 0:
            blacktime = blacktime - 2
        wmin = whitetime // 60
        wsec = whitetime % 60
        bmin = blacktime // 60
        bsec = blacktime % 60
        timestr = "{:02d}".format(wmin) + ":" + "{:02d}".format(wsec) + "       " + "{:02d}".format(
            bmin) + ":" + "{:02d}".format(bsec)
        if showingpromotion == False:
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

def computerMove(mv, forced = True):
    # Set the computer move that the player is expected to make
    # in the format b2b4 , g7g8q , etc
    global computermove
    global forcemove
    if len(mv) < 4:
        return
    # First set the globals so that the thread knows there is a computer move
    computermove = mv
    if forced == True:
        forcemove = 1
    # Next indicate this on the board. First convert the text representation to the field number
    fromnum = ((ord(mv[1:2]) - ord("1")) * 8) + (ord(mv[0:1]) - ord("a"))
    tonum = ((ord(mv[3:4]) - ord("1")) * 8) + (ord(mv[2:3]) - ord("a"))
    # Then light it up!
    board.ledFromTo(fromnum,tonum)  

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

def subscribeGame(eventCallback, moveCallback, keyCallback, takebackCallback = None):
    # Subscribe to the game manager
    global source
    global gamedbid
    global session
    global boardstates
    
    boardstates = []
    board.getBoardState()
    board.getBoardState()
    collectBoardState()
    
    source = inspect.getsourcefile(sys._getframe(1))
    Session = sessionmaker(bind=models.engine)
    session = Session()

    board.clearSerial()    
    gamethread = threading.Thread(target=gameThread, args=([eventCallback, moveCallback, keyCallback, takebackCallback]))
    gamethread.daemon = True
    gamethread.start()

def unsubscribeGame():
    # Stops the game manager
    global kill
    board.ledsOff()
    kill = 1
