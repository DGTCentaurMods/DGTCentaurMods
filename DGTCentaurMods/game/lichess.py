import sys
import berserk
import ssl
import time
import threading
from DGTCentaurMods.board import board
from DGTCentaurMods.board import centaur
from DGTCentaurMods.display import epaper
import chess
from DGTCentaurMods.config import config
import os

# Run a game on lichess
# This is version two so we do it directly and with screen control!

# Castling - move king, wait for beep, move rook
# pawn promotion not yet implemented. Pick up pawn, put down queen

# python3 lichess.py [current|New]

# This is our lichess access token, the game id we're playing, fill it
# in in v2conf.py
#
# Note the API requires that the raspberry pi clock has a reasonably
# accurate time for the SSL
token = centaur.get_lichess_api()
print(token)
pid = -1
board.clearSerial()
epaper.initEpaper()

if (len(sys.argv) == 1):
    #	print("python3 lichess.py [current|New1]")
    sys.exit()

if (len(sys.argv) > 1):
    if (str(sys.argv[1]) != "current" and str(sys.argv[1]) != "New"):
        # print("python3 lichess.py [current|New2]")
        sys.exit()

session = berserk.TokenSession(token)
client = berserk.Client(session=session)

remotemoves = ""
# changed dso
status = ""
cboard = chess.Board()

if (sys.argv[1] == "current"):
    epaper.writeText(0, 'Joining Game')
else:
    epaper.writeText(0, 'New Game')
epaper.writeText(1, 'on Lichess')
# board.writeText(2, 'LEDs Off')
board.ledsOff()

# Get the current player's username
who = client.account.get()
player = str(who.get('username'))
epaper.writeText(2, 'Player:')
epaper.writeText(3, player)

# We'll use this thread to start a game. Probably not the best way to do it but
# let's make the thread pause 5 seconds when it starts up so that we can be
# sure that client.board.stream_incoming_events() has started well

running = True


def newGameThread():
    time.sleep(5)

    if len(sys.argv) != 2:
        # mod by dso 3.10.21
        gtime = str(sys.argv[2])
        #	print(gtime)
        ginc = str(sys.argv[3])
        #	print(ginc)
        grated = str(sys.argv[4])
        #	print(grated)
        gcolor = str(sys.argv[5])
    #	print(gcolor)
    else:
        gtime = 0
        ginc = 0
        grated = 0
        gcolor = ""
    epaper.writeText(5, f'time {gtime} , {ginc}')
    epaper.writeText(6, f'ratedt={grated}')
    epaper.writeText(7, f'color={gcolor}')
    if (gtime == '10' and ginc == '5' and grated == "False" and gcolor == "white"):
        client.board.seek(10, 5, rated=False, variant='standard', color='white', rating_range=None)
    if (gtime == '10' and ginc == '5' and grated == "False" and gcolor == "black"):
        client.board.seek(10, 5, rated=False, variant='standard', color='black', rating_range=None)
    if (gtime == '10' and ginc == '5' and grated == "False" and gcolor == "random"):
        client.board.seek(10, 5, rated=False, variant='standard', color='random', rating_range=None)
    if (gtime == '10' and ginc == '5' and grated == "True" and gcolor == "white"):
        client.board.seek(10, 5, rated=True, variant='standard', color='white', rating_range=None)
    if (gtime == '10' and ginc == '5' and grated == "True" and gcolor == "black"):
        client.board.seek(10, 5, rated=True, variant='standard', color='black', rating_range=None)
    if (gtime == '10' and ginc == '5' and grated == "True" and gcolor == "random"):
        client.board.seek(10, 5, rated=True, variant='standard', color='random', rating_range=None)

    if (gtime == '15' and ginc == '10' and grated == "False" and gcolor == "white"):
        client.board.seek(15, 10, rated=False, variant='standard', color='white', rating_range=None)
    if (gtime == '15' and ginc == '10' and grated == "False" and gcolor == "black"):
        client.board.seek(15, 10, rated=False, variant='standard', color='black', rating_range=None)
    if (gtime == '15' and ginc == '10' and grated == "False" and gcolor == "random"):
        client.board.seek(15, 10, rated=False, variant='standard', color='random', rating_range=None)
    if (gtime == '15' and ginc == '10' and grated == "True" and gcolor == "white"):
        client.board.seek(15, 10, rated=True, variant='standard', color='white', rating_range=None)
    if (gtime == '15' and ginc == '10' and grated == "True" and gcolor == "white"):
        client.board.seek(15, 10, rated=True, variant='standard', color='black', rating_range=None)
    if (gtime == '15' and ginc == '10' and grated == "True" and gcolor == "random"):
        client.board.seek(15, 10, rated=True, variant='standard', color='random', rating_range=None)
    if (gtime == '30' and ginc == '0' and grated == "False" and gcolor == "white"):
        client.board.seek(30, 0, rated=False, variant='standard', color='white', rating_range=None)
    if (gtime == '30' and ginc == '0' and grated == "False" and gcolor == "black"):
        client.board.seek(30, 0, rated=False, variant='standard', color='black', rating_range=None)
    if (gtime == '30' and ginc == '0' and grated == "False" and gcolor == "random"):
        client.board.seek(30, 0, rated=False, variant='standard', color='random', rating_range=None)
    if (gtime == '30' and ginc == '0' and grated == "True" and gcolor == "white"):
        client.board.seek(30, 0, rated=True, variant='standard', color='white', rating_range=None)
    if (gtime == '30' and ginc == '0' and grated == "True" and gcolor == "black"):
        client.board.seek(30, 0, rated=True, variant='standard', color='black', rating_range=None)
    if (gtime == '30' and ginc == '0' and grated == "True" and gcolor == "random"):
        client.board.seek(30, 0, rated=True, variant='standard', color='random', rating_range=None)

    if (gtime == '30' and ginc == '20' and grated == "False" and gcolor == "white"):
        client.board.seek(30, 20, rated=False, variant='standard', color='white', rating_range=None)
    if (gtime == '30' and ginc == '20' and grated == "False" and gcolor == "black"):
        client.board.seek(30, 20, rated=False, variant='standard', color='black', rating_range=None)
    if (gtime == '30' and ginc == '20' and grated == "False" and gcolor == "random"):
        client.board.seek(30, 20, rated=False, variant='standard', color='random', rating_range=None)
    if (gtime == '30' and ginc == '20' and grated == "True" and gcolor == "white"):
        client.board.seek(30, 20, rated=True, variant='standard', color='white', rating_range=None)
    if (gtime == '30' and ginc == '20' and grated == "True" and gcolor == "black"):
        client.board.seek(30, 20, rated=True, variant='standard', color='black', rating_range=None)
    if (gtime == '30' and ginc == '20' and grated == "True" and gcolor == "random"):
        client.board.seek(30, 20, rated=True, variant='standard', color='random', rating_range=None)

    if (gtime == '60' and ginc == '20' and grated == "False" and gcolor == "white"):
        client.board.seek(60, 20, rated=False, variant='standard', color='white', rating_range=None)
    if (gtime == '60' and ginc == '20' and grated == "False" and gcolor == "black"):
        client.board.seek(60, 20, rated=False, variant='standard', color='black', rating_range=None)
    if (gtime == '60' and ginc == '20' and grated == "False" and gcolor == "random"):
        client.board.seek(60, 20, rated=False, variant='standard', color='random', rating_range=None)
    if (gtime == '60' and ginc == '20' and grated == "True" and gcolor == "white"):
        client.board.seek(60, 20, rated=True, variant='standard', color='white', rating_range=None)
    if (gtime == '60' and ginc == '20' and grated == "True" and gcolor == "black"):
        client.board.seek(60, 20, rated=True, variant='standard', color='black', rating_range=None)
    if (gtime == '60' and ginc == '20' and grated == "True" and gcolor == "random"):
        client.board.seek(60, 20, rated=True, variant='standard', color='random', rating_range=None)


# board.writeText(7, 'Game ID')

# Wait for a game to start and get the game id!
gameid = ""
if (str(sys.argv[1]) == "New"):
    epaper.writeText(4, 'gamesearch')
    # print("Looking for a game")
    gt = threading.Thread(target=newGameThread, args=())
    gt.daemon = True
    gt.start()
while gameid == "":
    for event in client.board.stream_incoming_events():
        if ('type' in event.keys()):
            if (event.get('type') == "gameStart"):

                # print("is gameStart")
                if ('game' in event.keys()):
                    # print(event)
                    gameid = event.get('game').get('id')
                    break

epaper.writeText(9, gameid)

playeriswhite = -1
whiteplayer = ""
blackplayer = ""

whiteclock = 0
blackclock = 0
whiteincrement = 0
blackincrement = 0
winner = ''

fenlog = "/home/pi/centaur/fen.log"
f = open(fenlog, "w")
f.write("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
f.close()

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
    global resign
    global winner
    global wtime
    global btime
    while running:
        gamestate = client.board.stream_game_state(gameid)
        for state in gamestate:
            print(state)
            # mod by dso 4.1021
            if ('state' in state.keys()):
                remotemoves = state.get('state').get('moves')
                status = state.get('state').get('status')
            else:
                if ('moves' in state.keys()):
                    remotemoves = state.get('moves')
                if ('status' in state.keys()):
                    status = state.get('status')
            remotemoves = str(remotemoves)
            status = str(status)
            # dso add events and stop the game
            if ('text' in state.keys()):
                message = state.get('text')
                if message == "Takeback sent":
                    client.board.post_message(gameid, 'Sorry , external boards can\'t handle takeback', spectator=False)

                if message == "Black offers draw":
                    client.board.decline_draw(gameid)

                if message == "White offers draw":
                    client.board.decline_draw(gameid)

            if status == 'resign':
                epaper.writeText(11, 'Resign')
                winner = str(state.get('winner'))
                epaper.writeText(12, winner + ' wins')
                time.sleep(3)
                os._exit(0)
            # running = False
            if status == 'aborted':
                epaper.writeText(11, 'Game aborted')
                winner = 'No Winner'
                epaper.writeText(12, 'No winner')
                time.sleep(3)
                os._exit(0)

            if status == 'outoftime':
                epaper.writeText(11, 'Out of time')
                winner = str(state.get('winner'))
                epaper.writeText(12, winner + ' wins')
                time.sleep(3)
                os._exit(0)
            if status == 'timeout':
                epaper.writeText(11, 'Out of time')
                winner = str(state.get('winner'))
                epaper.writeText(12, winner + ' wins')
                time.sleep(3)
                os._exit(0)
            if status == 'draw':
                epaper.writeText(11, 'Draw')
                winner = str(state.get('winner'))
                epaper.writeText(12, winner + ' No Winner')
                time.sleep(3)
                os._exit(0)

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

            time.sleep(0.1)


# print("Starting thread to track the game on Lichess")
st = threading.Thread(target=stateThread, args=())
st.daemon = True
st.start()
# print("Started")

board.beep(board.SOUND_GENERAL)
boardmoves = ""
lastboardmove = ""
beeped = 0
newgame = 1
lastmove = ""
while playeriswhite == -1:
    time.sleep(0.1)

if playeriswhite == 0:
    lastmove = "1234"
    remotemoves = "1234"
#    board.writeText(8, 'Black')

# ready for white
ourturn = 1
# if playeriswhite == 0 or playeriswhite == 1:
#	ourturn = 0

board.clearBoardData()

oldremotemoves = ""
correcterror = -1
halfturn = 0
castled = ""

epaper.clearScreen()
epaper.writeText(0, blackplayer)
epaper.writeText(9, whiteplayer)
fen = cboard.fen()
sfen = fen[0: fen.index(" ")]
baseboard = chess.BaseBoard(sfen)
pieces = []
for x in range(0, 64):
    pieces.append(str(chess.BaseBoard(sfen).piece_at(x)))
epaper.drawBoard(pieces)

client.board.post_message(gameid,
                          'I\'m playing with a DGT-Centaur. I\'m not a bot, this Version is in a beta status - have fun',
                          spectator=False)
resign = 1
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

    if ourturn == 1 and status == "started" and lastmove != '1234':
        # Wait for the player's move
        movestart = time.time()
        startzeit = time.time()
        # print(str(startzeit-startzeit))
        move = board.waitMove()
        board.beep(board.SOUND_GENERAL)

        # Pass the move through

        # resign by dso place a new figure on the board

        if (len(move) == 2):
            fromsq = move[0] * -1
            mylastfrom = fromsq
            tosq = move[1]
        # board.writeText(12, 'normal move')
        if (len(move) == 3):
            # board.writeText(12, 'kick move')
            # This move should consist of two lifted and one place (two positives, 1 negative)
            # it is a piece take. So the negative that is not the inverse of the positive
            # is the piece that has moved and the positive is the tosq

            # mod by dso 4.10.21
            tosq = -1

            tosq = move[2]

            fromsq = -1
            if move[0] != (tosq * -1):
                fromsq = move[0] * -1
            if move[1] != (tosq * -1):
                fromsq = move[1] * -1

        # Added to reduce the numbering back to 0-64 after change to board
        fromsq = fromsq - 1
        tosq = tosq - 1

        mylastfrom = fromsq
        # Convert to letter number square format
        fromln = board.convertField(fromsq)
        # print(fromln)

        toln = board.convertField(tosq)

        # If the piece is a pawn we should take care of promotion here. You could choose it from
        # the board screen. But I'll do that later!
        # Send the move
        lastmove = fromln + toln

        if lastmove == castled:
            # If we're castling and this is just the rook move then ignore it
            lastmove = ""
            correcterror = tosq
        if correcterror == tosq:
            board.ledsOff()
            correcterror = -1
        else:
            try:

                mv = chess.Move.from_uci(lastmove)
                print("Checked")
                if (mv in cboard.legal_moves):
                    cboard.push(mv)

                    if lastmove == "e1g1":
                        castled = "h1f1"
                    if lastmove == "e1c1":
                        castled = "a1d1"
                    if lastmove == "e8g8":
                        castled = "h8f8"
                    if lastmove == "e8c8":
                        castled = "a8d8"
                    playertime = time.time()

                    # check if lichess accept this move
                    ret = client.board.make_move(gameid, fromln + toln)
                    if ret:
                        ourturn = 0
                        halfturn = halfturn + 1
                # old place outturn ans halfturn
                else:
                    # print("not a legal move checking for half turn")
                    if halfturn != 0:
                        # print("Not a legal move!")
                        # print(board.legal_moves)
                        board.clearBoardData()
                        board.beep(board.SOUND_WRONG_MOVE)
                        correcterror = fromsq
            except:
                # print("exception checking for half turn")
                if halfturn != 0:
                    # print("Not a legal move!")
                    # print(board.legal_moves)
                    board.clearBoardData()
                    board.beep(board.SOUND_WRONG_MOVE)
                    correcterror = fromsq

        # print(board)

        if playeriswhite == 1:

            whiteclock = whiteclock - ((time.time() - movestart) * 1000)
            whiteclock = whiteclock + whiteincrement

        else:
            blackclock = blackclock + blackincrement
            blackclock = blackclock - ((time.time() - movestart) * 1000)

        wtext = ""
        if whiteclock // 60000 == 0:
            wtext = str(whiteclock // 1000).replace(".0", "") + " secs      "
        else:
            wtext = str(whiteclock // 60000).replace(".0", "") + " mins      "
        #board.writeText(10, wtext)
        epaper.writeText(10,wtext)
        btext = ""
        if blackclock // 60000 == 0:
            btext = str(blackclock // 1000).replace(".0", "") + " secs      "
        else:
            btext = str(blackclock // 60000).replace(".0", "") + " mins      "
        #board.writeText(1, btext)
        epaper.writeText(10, btext)
        fen = cboard.fen()
        sfen = fen[0: fen.index(" ")]
        baseboard = chess.BaseBoard(sfen)
        pieces = []
        for x in range(0, 64):
            pieces.append(str(chess.BaseBoard(sfen).piece_at(x)))
        fenlog = "/home/pi/centaur/fen.log"
        f = open(fenlog, "w")
        f.write(sfen)
        f.close()
        #board.writeText(12, str(mv))
        epaper.writeText(12, str(mv))
        epaper.drawBoard(pieces)
    if playeriswhite == 0 and newgame == 1:
        ourturn = 0
        if str(remotemoves) != '1234':
            lastmove = '3456'
    print(playeriswhite)
    print('Achtung: ' + lastmove)
    print('Achtung= ' + str(remotemoves)[-4:])
    print('ourturn sollte 0 sein ' + str(ourturn))
    if ourturn == 0 and status == "started":
        # Here we wait to get a move from the other player on lichess

        movestart = time.time()
        while status == "started" and str(remotemoves)[-4:] == lastmove:
            time.sleep(0.1)
    if status == "started":
        # There's an incoming move to deal with
        lichesstime = time.time()
        board.beep(board.SOUND_GENERAL)
        rr = "   " + str(remotemoves)
        lrmove = rr[-5:].strip()
        lrmove = lrmove[:4]
        lrfrom = lrmove[:2]
        lrto = lrmove[2:4]
        lrfromcalc = (ord(lrfrom[:1]) - 97) + ((int(lrfrom[1:2]) - 1) * 8)
        lrtocalc = (ord(lrto[:1]) - 97) + ((int(lrto[1:2]) - 1) * 8)
        board.clearBoardData()
        board.ledFromTo(lrfromcalc, lrtocalc)
        # Then wait for a piece to be moved TO that position
        movedto = -1
        while movedto != lrtocalc and status == "started":
            move = board.waitMove()
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
                board.beep(board.SOUND_WRONG_MOVE)
            # Subtract one here to return to 0-64 after change in board
            movedto = lrtocalc
        board.beep(board.SOUND_GENERAL)
        board.clearSerial()
        mv = chess.Move.from_uci(rr[-5:].strip())
        cboard.push(mv)
        board.ledsOff()
        newgame = 0
        ourturn = 1

    # print(board)
    # dso timefix 5.10.21

    if playeriswhite == 0:
        whiteclock = whiteclock - ((time.time() - movestart) * 1000)
        whiteclock = whiteclock + whiteincrement
    else:
        blackclock = blackclock - ((time.time() - movestart) * 1000)
        blackclock = blackclock + blackincrement

    wtext = ""
    if whiteclock // 60000 == 0:
        wtext = str(whiteclock // 1000).replace(".0", "") + " secs      "
    else:
        wtext = str(whiteclock // 60000).replace(".0", "") + " mins      "
    #board.writeText(10, wtext)
    epaper.writeText(10, wtext)
    btext = ""
    if blackclock // 60000 == 0:
        btext = str(blackclock // 1000).replace(".0", "") + " secs      "
    else:
        btext = str(blackclock // 60000).replace(".0", "") + " mins      "
    #board.writeText(1, btext)
    epaper.writeText(1, btext)
    if starttime < 0:
        starttime = time.time()
    # eingerückt
    fen = cboard.fen()
    sfen = fen[0: fen.index(" ")]
    baseboard = chess.BaseBoard(sfen)
    pieces = []
    for x in range(0, 64):
        pieces.append(str(chess.BaseBoard(sfen).piece_at(x)))
    f = open(fenlog, "w")
    f.write(sfen)
    f.close()
    #board.writeText(12, str(mv))
    epaper.writeText(12, str(mv))
    epaper.drawBoard(pieces)

running = False
epaper.writeText(11, 'Game over')
epaper.writeText(12, f'Winner: {winner}')
epaper.writeText(13, 'reason =' + status)
time.sleep(5)
epaper.clearScreen()
os._exit(0)
