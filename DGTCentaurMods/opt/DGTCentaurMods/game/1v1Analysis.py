# Play pure stockfish without DGT Centaur Adaptive Play
#
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

from DGTCentaurMods.game import gamemanager
from DGTCentaurMods.display import epaper
from DGTCentaurMods.display.ui_components import AssetManager
import time
import chess
import chess.engine
import sys
from random import randint
from PIL import Image, ImageDraw, ImageFont
import pathlib

curturn = 1
engine = chess.engine.SimpleEngine.popen_uci(str(pathlib.Path(__file__).parent.resolve()) + "/../engines/ct800", timeout = None)
computeronturn = 0
kill = 0
firstmove = 0
graphson = 1

scorehistory = []

gamemanager.setGameInfo("1v1 Analysis", "", "", "Player White", "Player Black")

def keyCallback(key):
    # This function will receive any keys presses on the keys
    # under the display. Possibles:
    # gamemanager.BTNBACK  gamemanager.BTNTICK  gamemanager.BTNUP
    # gamemanager.BTNDOWN  gamemanager.BTNHELP  gamemanager.BTNPLAY
    global kill
    global engine
    global graphson
    global firstmove
    print("Key event received: " + str(key))
    if key == gamemanager.BTNBACK:        
        kill = 1
        engine.quit()
    if key == gamemanager.BTNDOWN:
        image = Image.new('1', (128, 80), 255)
        epaper.drawImagePartial(0, 209, image)     
        epaper.drawImagePartial(0, 1, image)
        graphson = 0        
    if key == gamemanager.BTNUP:
        graphson = 1
        firstmove = 1
        info = engine.analyse(gamemanager.cboard, chess.engine.Limit(time=0.5))
        evaluationGraphs(info)        

def eventCallback(event):
    global curturn
    global engine
    global eloarg
    global kill
    global firstmove
    global engine
    global scorehistory
    # This function receives event callbacks about the game in play
    if event == gamemanager.EVENT_NEW_GAME:
        writeTextLocal(0, "               ")
        writeTextLocal(1, "               ")
        epaper.quickClear()        
        scorehistory = []
        curturn = 1
        firstmove = 1
        drawBoardLocal(gamemanager.cboard.fen())
    if event == gamemanager.EVENT_WHITE_TURN:        
        drawBoardLocal(gamemanager.cboard.fen())
        curturn = 1
        info = engine.analyse(gamemanager.cboard, chess.engine.Limit(time=0.5))
        evaluationGraphs(info)        
    if event == gamemanager.EVENT_BLACK_TURN:
        drawBoardLocal(gamemanager.cboard.fen())
        curturn = 0
        info = engine.analyse(gamemanager.cboard, chess.engine.Limit(time=0.5))        
        evaluationGraphs(info)                
    if event == gamemanager.EVENT_REQUEST_DRAW:
        gamemanager.drawGame()
    if event == gamemanager.EVENT_RESIGN_GAME:
        gamemanager.resignGame(curturn)
    if type(event) == str:
        # Termination.CHECKMATE
        # Termination.STALEMATE
        # Termination.INSUFFICIENT_MATERIAL
        # Termination.SEVENTYFIVE_MOVES
        # Termination.FIVEFOLD_REPETITION
        # Termination.FIFTY_MOVES
        # Termination.THREEFOLD_REPETITION
        # Termination.VARIANT_WIN
        # Termination.VARIANT_LOSS
        # Termination.VARIANT_DRAW
        if event.startswith("Termination."):
            image = Image.new('1', (128, 12), 255)
            draw = ImageDraw.Draw(image)
            font12 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 12)
            txt = event[12:]
            draw.text((30, 0), txt, font=font12, fill=0)
            epaper.drawImagePartial(0, 221, image)
            time.sleep(0.3)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
            image = image.transpose(Image.FLIP_LEFT_RIGHT)    
            epaper.drawImagePartial(0, 57, image)            
            epaper.quickClear()            
            # Let's display an end screen
            image = Image.new('1', (128,292), 255)
            draw = ImageDraw.Draw(image)
            font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
            draw.text((0,0), "   GAME OVER", font=font18, fill = 0)
            draw.text((0,20), "          " + gamemanager.getResult(), font=font18, fill = 0)            
            if len(scorehistory) > 0:
                draw.line([(0,114),(128,114)], fill = 0, width = 1)
                barwidth = 128/len(scorehistory)
                if barwidth > 8:
                    barwidth = 8
                baroffset = 0        
                for i in range(0, len(scorehistory)):
                    if scorehistory[i] >= 0:
                        col = 255
                    else:
                        col = 0
                    draw.rectangle([(baroffset,114),(baroffset+barwidth,114 - (scorehistory[i]*4))],fill=col,outline='black')
                    baroffset = baroffset + barwidth
            
            epaper.drawImagePartial(0, 0, image)
            time.sleep(10)
            engine.quit()
            kill = 1

def moveCallback(move):
    # This function receives valid moves made on the board
    # Note: the board state is in python-chess object gamemanager.board
    pass

def takebackCallback():
    # This function gets called when the user takes back a move   
    global curturn     
    # First the turn switches
    if curturn == 1:
        curturn = 0
    else:
        curturn = 1    
    # Now call eventCallback from the new state
    if curturn == 0:
        eventCallback(gamemanager.EVENT_BLACK_TURN)    
    else:
        eventCallback(gamemanager.EVENT_WHITE_TURN)
    
def evaluationGraphs(info):
    # Draw the evaluation graphs to the screen
    global firstmove
    global graphson
    global scorehistory
    global curturn
    if graphson == 0:
        image = Image.new('1', (128, 80), 255)
        epaper.drawImagePartial(0, 209, image) 
        time.sleep(0.3)
        epaper.drawImagePartial(0, 1, image)        
    sval = 0
    sc = str(info["score"])        
    if "Mate" in sc:
        sval = 10000
        sval = sc[13:24]
        sval = sval[1:sval.find(")")] 
    else:
        sval = sc[11:24]
        sval = sval[1:sval.find(")")]                
    sval = float(sval)
    sval = sval / 100
    if "BLACK" in sc:
        sval = sval * -1
    # Draw evaluation bars
    if graphson == 1:
        image = Image.new('1', (128, 80), 255)
        draw = ImageDraw.Draw(image)
        font12 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 12)
    txt = "{:5.1f}".format(sval)        
    if sval > 999:
        txt = ""
    if "Mate" in sc:
        txt = "Mate in " + "{:2.0f}".format(abs(sval*100))
        sval = sval * 100000    
    if graphson == 1:
        draw.text((50, 12), txt, font=font12, fill=0)
        draw.rectangle([(0,1),(127,11)],fill=None,outline='black')    
    # Now calculate where the black goes in the indicator window
    if sval > 12:
        sval = 12
    if sval < -12:
        sval = -12    
    if firstmove == 0:
        scorehistory.append(sval)        
    else:
        firstmove = 0    
    offset = (128/25) * (sval + 12)
    if offset < 128:
        if graphson == 1:
            draw.rectangle([(offset,1),(127,11)],fill=0,outline='black')        
    # Now lets do the bar chart view
    if graphson == 1:
        if len(scorehistory) > 0:
            draw.line([(0,50),(128,50)], fill = 0, width = 1)
            barwidth = 128/len(scorehistory)
            if barwidth > 8:
                barwidth = 8
            baroffset = 0        
            for i in range(0, len(scorehistory)):
                if scorehistory[i] >= 0:
                    col = 255
                else:
                    col = 0
                draw.rectangle([(baroffset,50),(baroffset+barwidth,50 - (scorehistory[i]*2))],fill=col,outline='black')
                baroffset = baroffset + barwidth  
        tmp = image.copy()
        dr2 = ImageDraw.Draw(tmp)
        if curturn == 1:            
            dr2.ellipse((119,14,126,21), fill = 0, outline = 0)
        epaper.drawImagePartial(0, 209, tmp)         
        if curturn == 0:
            draw.ellipse((119,14,126,21), fill = 0, outline = 0)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image = image.transpose(Image.FLIP_LEFT_RIGHT)  
        epaper.drawImagePartial(0, 1, image)    

def writeTextLocal(row,txt):
    # Write Text on a give line number
    image = Image.new('1', (128, 20), 255)
    draw = ImageDraw.Draw(image)
    font18 = ImageFont.truetype(AssetManager.get_resource_path("Font.ttc"), 18)
    draw.text((0, 0), txt, font=font18, fill=0)
    epaper.drawImagePartial(0, (row*20), image)    

def drawBoardLocal(fen):
    # This local version of drawboard - we draw into a 64x64 image and then
    # use epaper.drawWindow to write that to the screen
    curfen = str(fen)
    curfen = curfen.replace("/", "")
    curfen = curfen.replace("1", " ")
    curfen = curfen.replace("2", "  ")
    curfen = curfen.replace("3", "   ")
    curfen = curfen.replace("4", "    ")
    curfen = curfen.replace("5", "     ")
    curfen = curfen.replace("6", "      ")
    curfen = curfen.replace("7", "       ")
    curfen = curfen.replace("8", "        ")
    nfen = ""
    for a in range(8, 0, -1):
        for b in range(0, 8):
            nfen = nfen + curfen[((a - 1) * 8) + b]
    lboard = Image.new('1', (128, 128), 255)
    draw = ImageDraw.Draw(lboard)
    chessfont = Image.open(AssetManager.get_resource_path("chesssprites.bmp"))
    for x in range(0,64):
        pos = (x - 63) * -1
        row = (16 * (pos // 8))
        col = (x % 8) * 16
        px = 0
        r = x // 8
        c = x % 8
        py = 0
        if (r // 2 == r / 2 and c // 2 == c / 2):
            py = py + 16
        if (r //2 != r / 2 and c // 2 != c / 2):
            py = py + 16
        if nfen[x] == "P":
            px = 16
        if nfen[x] == "R":
            px = 32
        if nfen[x] == "N":
            px = 48
        if nfen[x] == "B":
            px = 64
        if nfen[x] == "Q":
            px = 80
        if nfen[x] == "K":
            px = 96
        if nfen[x] == "p":
            px = 112
        if nfen[x] == "r":
            px = 128
        if nfen[x] == "n":
            px = 144
        if nfen[x] == "b":
            px = 160
        if nfen[x] == "q":
            px = 176
        if nfen[x] == "k":
            px = 192
        piece = chessfont.crop((px, py, px+16, py+16))
        if nfen[x] == "p":
            piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        if nfen[x] == "r":
            piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        if nfen[x] == "n":
            piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        if nfen[x] == "b":
            piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        if nfen[x] == "q":
            piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        if nfen[x] == "k":
            piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)            
        lboard.paste(piece,(col, row))
    draw.rectangle([(0,0),(127,127)],fill=None,outline='black')
    epaper.drawImagePartial(0, 81, lboard)

# Activate the epaper
epaper.initEpaper()
#epaper.pauseEpaper()

# Subscribe to the game manager to activate the previous functions
gamemanager.subscribeGame(eventCallback, moveCallback, keyCallback, takebackCallback)
writeTextLocal(0,"Place pieces in")
writeTextLocal(1,"Starting Pos")

while kill == 0:
    time.sleep(0.1)
