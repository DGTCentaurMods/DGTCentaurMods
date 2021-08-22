import sys
import berserk
import ssl
import time
import threading
import pyrasite
import psutil
import boardfunctions
import chess
import config

# Run a game on lichess
# This is version two so we do it directly and with screen control!

# Castling - move king, wait for beep, move rook
# pawn promotion not yet implemented. Pick up pawn, put down queen

# python3 lichess.py [current|live]

# This is our lichess access token, the game id we're playing, fill it
# in in config.py
token = config.lichesstoken
pid = -1

boardfunctions.clearSerial()

if (len(sys.argv) == 1):
    print("python3 lichess.py [current|live]")
    sys.exit()

if (len(sys.argv) > 1):
    if (str(sys.argv[1]) != "current" and str(sys.argv[1]) != "live"):
        print("python3 lichess.py [current|live]")
        sys.exit()

session = berserk.TokenSession(token)
client = berserk.Client(session=session)

remotemoves = ""
status = "started"
board = chess.Board()

# First start up the screen
boardfunctions.initScreen()
if (sys.argv[1] == "current"):
    boardfunctions.writeText(0, 'Joining Game')
else:
    boardfunctions.writeText(0, 'Starting Game')
boardfunctions.writeText(1, 'on Lichess')
boardfunctions.writeText(2, 'LEDs Off')
boardfunctions.ledsOff()

# Get the current player's username
who = client.account.get()
player = str(who.get('username'))
boardfunctions.writeText(3, 'Player:')
boardfunctions.writeText(4, player)

# We'll use this thread to start a game. Probably not the best way to do it but
# let's make the thread pause 5 seconds when it starts up so that we can be
# sure that client.board.stream_incoming_events() has started well

running = True

def newGameThread():
    time.sleep(5)
    # seek(self, time, increment, rated=False, variant='standard', color='random', rating_range=None):
    # For now try a 30 minute game
    client.board.seek(30, 0)


boardfunctions.writeText(5, 'Game ID')

# Wait for a game to start and get the game id!
gameid = ""
if (str(sys.argv[1]) == "live"):
    #print("Looking for a game")
    gt = threading.Thread(target=newGameThread, args=())
    gt.daemon = True
    gt.start()
while gameid == "":
    for event in client.board.stream_incoming_events():
        if ('type' in event.keys()):
            if (event.get('type') == "gameStart"):
                print("is gameStart")
                if ('game' in event.keys()):
                    print(event)
                    gameid = event.get('game').get('id')
                    break
print("Game started: " + gameid)
boardfunctions.writeText(6, gameid)

playeriswhite = -1
whiteplayer = ""
blackplayer = ""

whiteclock = 0
blackclock = 0
whiteincrement = 0
blackincrement = 0

# Lichess doesn't start the clocks until white moves
starttime = -1

# This thread keeps track of the moves made on lichess
def stateThread():
    global remotemoves
    global status
    global playeriswhite
    global player
    global whiteplayer
    global blackplayer
    global whiteclock
    global blackclock
    global whiteincrement
    global blackincrement
    while running:
        gamestate = client.board.stream_game_state(gameid)
        for state in gamestate:
            print(state)
            if ('state' in state.keys()):
                remotemoves = state.get('state').get('moves')
                status = state.get('state').get('status')
            else:
                remotemoves = state.get('moves')
                status = state.get('status')
            remotemoves = str(remotemoves)
            status = str(status)
            if (remotemoves == "None"):
                remotemoves = ""
            if ('black' in state.keys()):
                if ('name' in state.get('white')):
                    print(str(state.get('white').get('name')) +
                          " vs " + str(state.get('black').get('name')))
                    whiteplayer = str(state.get('white').get('name'))
                    blackplayer = str(state.get('black').get('name'))
                    if (str(state.get('white').get('name')) == player):
                        playeriswhite = 1
                    else:
                        playeriswhite = 0
            if ('state' in state.keys()):
                if ('wtime' in state.get('state').keys()):
                    wtime = int(state.get('state').get('wtime'))
                    whiteclock = wtime
                    winc = int(state.get('state').get('winc'))
                    whiteincrement = winc
                if ('btime' in state.get('state').keys()):
                    btime = int(state.get('state').get('btime'))
                    blackclock = btime
                    binc = int(state.get('state').get('binc'))
                    blackincrement = binc

            time.sleep(1)


print("Starting thread to track the game on Lichess")
st = threading.Thread(target=stateThread, args=())
st.daemon = True
st.start()
print("Started")

boardfunctions.beep(boardfunctions.SOUND_GENERAL)
boardmoves = ""
lastboardmove = ""
beeped = 0

while playeriswhite == -1:
    time.sleep(0.1)
#boardfunctions.writeText(7, "Playing as")
#if playeriswhite == 1:
#    boardfunctions.writeText(8, 'White')
#if playeriswhite == 0:
#    boardfunctions.writeText(8, 'Black')

# ready for white
ourturn = 1
if playeriswhite == 0:
    ourturn = 0

boardfunctions.clearBoardData()

oldremotemoves = ""
lastmove = ""
correcterror = -1
halfturn = 0
castled = ""

boardfunctions.clearScreenBuffer()
boardfunctions.writeText(0,blackplayer)
boardfunctions.writeText(9,whiteplayer)
fen = board.fen()
sfen = fen[0 : fen.index(" ")]
baseboard = chess.BaseBoard(sfen)
pieces = []
for x in range(0,64):
    pieces.append(str(chess.BaseBoard(sfen).piece_at(x)))
boardfunctions.drawBoard(pieces)

while status == "started" and ourturn != 0:

    if ourturn == 1:
        if playeriswhite == 1:
            currentmover = 1
        else:
            currentmover = 0
    if ourturn == 0:
        if playeriswhite == 1:
            currentmover = 1
        else:
            currentmover = 0
    currentmovestart = time.time()

    if ourturn == 1 and status == "started":
        # Wait for the player's move
        movestart = time.time()
        move = boardfunctions.waitMove()
        boardfunctions.beep(boardfunctions.SOUND_GENERAL)
        # Pass the move through
        if (len(move) == 2):
                fromsq = move[0] * -1
                mylastfrom = fromsq
                tosq = move[1]
        if (len(move) == 3):
                # This move should consist of two lifted and one place (two positives, 1 negative)
                # it is a piece take. So the negative that is not the inverse of the positive
                # is the piece that has moved and the positive is the tosq
                tosq = -1
                if move[0] >= 0:
                        tosq = move[0]
                if move[2] >= 0:
                        tosq = move[2]
                if move[1] >= 0:
                        tosq = move[1]
                fromsq = -1
                if move[0] != (tosq * -1) and move[0] != tosq:
                        fromsq = move[0] * -1
                if move[1] != (tosq * -1) and move[1] != tosq:
                        fromsq = move[1] * -1
                if move[2] != (tosq * -1) and move[2] != tosq:
                        fromsq = move[2] * -1
        mylastfrom = fromsq
        # Convert to letter number square format
        fromln = boardfunctions.convertField(fromsq)
        print(fromln)
        toln = boardfunctions.convertField(tosq)
        print(toln)
        # If the piece is a pawn we should take care of promotion here. You could choose it from
        # the board screen. But I'll do that later!
        # Send the move
        lastmove = fromln + toln
        print(lastmove)
        print(castled)
        print(correcterror)
        if lastmove == castled:
                # If we're castling and this is just the rook move then ignore it
                lastmove = ""
                correcterror = tosq
        if correcterror == tosq:
                boardfunctions.ledsOff()
                correcterror = -1
        else:
                try:
                    print("Checking validity")
                    mv = chess.Move.from_uci(lastmove)
                    print("Checked")
                    if (mv in board.legal_moves):
                            board.push(mv)
                            if lastmove == "e1g1":
                                    castled = "h1f1"
                            if lastmove == "e1c1":
                                    castled = "a1d1"
                            if lastmove == "e8g8":
                                    castled = "h8f8"
                            if lastmove == "e8c8":
                                    castled = "a8d8"
                            ourturn = 0
                            print("Making move with client")
                            ret = client.board.make_move(gameid, fromln + toln)
                            print("Made move with client")
                            halfturn = halfturn + 1
                    else:
                            print("not a legal move checking for half turn")
                            if halfturn != 0:
                                    print("Not a legal move!")
                                    print(board.legal_moves)
                                    boardfunctions.clearBoardData()
                                    boardfunctions.beep(boardfunctions.SOUND_WRONG_MOVE)
                                    correcterror = fromsq
                except:
                    print("exception checking for half turn")
                    if halfturn != 0:
                        print("Not a legal move!")
                        print(board.legal_moves)
                        boardfunctions.clearBoardData()
                        boardfunctions.beep(boardfunctions.SOUND_WRONG_MOVE)
                        correcterror = fromsq
        print(board)

        if playeriswhite == 1:
            whiteclock = whiteclock - ((time.time() - movestart) * 1000)
            whiteclock = whiteclock + whiteincrement
        else:
            blackclock = blackclock + blackincrement
            blackclock = blackclock - ((time.time() - movestart) * 1000)

        wtext = ""
        if whiteclock//60000 == 0:
            wtext = str(whiteclock//1000).replace(".0","") + " secs      "
        else:
            wtext = str(whiteclock//60000).replace(".0","") + " mins      "
        boardfunctions.writeText(10,wtext)
        btext = ""
        if blackclock // 60000 == 0:
            btext = str(blackclock // 1000).replace(".0", "") + " secs      "
        else:
            btext = str(blackclock // 60000).replace(".0", "") + " mins      "
        boardfunctions.writeText(1, btext)

    fen = board.fen()
    sfen = fen[0 : fen.index(" ")]
    baseboard = chess.BaseBoard(sfen)
    pieces = []
    for x in range(0,64):
        pieces.append(str(chess.BaseBoard(sfen).piece_at(x)))
    boardfunctions.drawBoard(pieces)

    if ourturn == 0 and status == "started":
        # Here we wait to get a move from the other player on lichess
        movestart = time.time()
        while status == "started" and str(remotemoves)[-4:] == lastmove:
            time.sleep(0.5)
        if status == "started":
            # There's an incoming move to deal with
            boardfunctions.beep(boardfunctions.SOUND_GENERAL)
            rr = "   " + str(remotemoves)
            lrmove = rr[-5:].strip()
            lrmove = lrmove[:4]
            lrfrom = lrmove[:2]
            lrto = lrmove[2:4]
            lrfromcalc = (ord(lrfrom[:1]) - 97) + ((int(lrfrom[1:2]) - 1) * 8)
            lrtocalc = (ord(lrto[:1]) - 97) + ((int(lrto[1:2]) - 1) * 8)
            boardfunctions.clearBoardData()
            boardfunctions.ledFromTo(lrfromcalc, lrtocalc)
            # Then wait for a piece to be moved TO that position
            movedto = -1
            while movedto != lrtocalc and status == "started":
                move = boardfunctions.waitMove()
                valid = 0
                if move[0] == lrtocalc:
                        valid = 1
                if len(move) > 1:
                    if move[1] == lrtocalc:
                            valid = 1
                if len(move) == 3:
                        if move[2] == lrtocalc:
                                valid = 1
                if valid == 0:
                    boardfunctions.beep(boardfunctions.SOUND_WRONG_MOVE)
                movedto = lrtocalc 
            boardfunctions.beep(boardfunctions.SOUND_GENERAL)
            boardfunctions.clearSerial()
            mv = chess.Move.from_uci(rr[-5:].strip())
            board.push(mv)
            boardfunctions.ledsOff()
            ourturn = 1

        print(board)

        if playeriswhite == 0:
            whiteclock = whiteclock - ((time.time() - movestart) * 1000)
            whiteclock = whiteclock + whiteincrement
        else:
            blackclock = blackclock - ((time.time() - movestart) * 1000)
            blackclock = blackclock + blackincrement

        wtext = ""
        if whiteclock//60000 == 0:
            wtext = str(whiteclock//1000).replace(".0","") + " secs      "
        else:
            wtext = str(whiteclock//60000).replace(".0","") + " mins      "
        boardfunctions.writeText(10,wtext)
        btext = ""
        if blackclock // 60000 == 0:
            btext = str(blackclock // 1000).replace(".0", "") + " secs      "
        else:
            btext = str(blackclock // 60000).replace(".0", "") + " mins      "
        boardfunctions.writeText(1, btext)

        if starttime < 0:
            starttime = time.time()

    fen = board.fen()
    sfen = fen[0 : fen.index(" ")]
    baseboard = chess.BaseBoard(sfen)
    pieces = []
    for x in range(0,64):
        pieces.append(str(chess.BaseBoard(sfen).piece_at(x)))
    boardfunctions.drawBoard(pieces)

running = False
print("Game Over")
boardfunctions.sleepScreen()
sys.exit()
