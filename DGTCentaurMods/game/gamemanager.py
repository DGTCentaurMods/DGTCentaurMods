# This script manages a chess game, passing events and moves back to the calling script with callbacks
# The calling script is expected to manage the display itself using epaper.py
# Calling script initialises with subscribeGame(eventCallback, moveCallback, keyCallback)
# eventCallback feeds back events such as start of game, gameover
# moveCallback feeds back the chess moves made on the board
# keyCallback feeds back key presses from keys under the display

# TODO
# Promotion
# Testing/Improve reliability move detection
# Indicate next move
# Force next move

from DGTCentaurMods.board import boardfunctions
import threading
import time
import chess

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
    lift = 0
    place = 0
    if field >= 0:
        lift = 1
    else:
        place = 1
        field = field * -1
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
            try:
                tcm = chess.Move.from_uci(tm)
                if tcm in legalmoves:
                    legalsquares.append(x)
            except:
                pass
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
            # TODO - add promotion choice here
            mv = fromname + toname
            # Make the move and update fen.log
            board.push(chess.Move.from_uci(mv))
            fenlog = "/home/pi/centaur/fen.log"
            f = open(fenlog, "w")
            f.write(board.fen())
            f.close()
            legalsquares = []
            sourcesq = -1
            if movecallbackfunction != None:
                movecallbackfunction(mv)
            boardfunctions.beep(boardfunctions.SOUND_GENERAL)
            # Check the outcome
            outc = board.outcome()
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
    keycallbackfunction = keycallback
    movecallbackfunction = moveCallback
    eventcallbackfunction = eventCallback
    boardfunctions.subscribeEvents(keycallback, fieldcallback)
    t = 0
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
                    t = 0
                except:
                    pass
        time.sleep(0.1)

def subscribeGame(eventCallback, moveCallback, keyCallback):
    # Subscribe to the game manager
    boardfunctions.clearSerial()
    gamethread = threading.Thread(target=gameThread, args=([eventCallback, moveCallback, keyCallback]))
    gamethread.daemon = True
    gamethread.start()

def unsubscribeGame():
    # Stops the game manager
    global kill
    kill = 1