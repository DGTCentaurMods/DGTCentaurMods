# Quick temporary script to set up the lichess token until we have a db method
#

from DGTCentaurMods.board import boardfunctions
import os
import time
import sys
import re
import pathlib

boardfunctions.initScreen()
time.sleep(2)

# Get the token
token = boardfunctions.getText("API Token")

if token == "":
	sys.exit()

token = "lichesstoken=\"" + token + "\"\r\n"
file = str(pathlib.Path(__file__).parent.resolve()) + "/config.py"
cfile = open(file,"w")
cfile.write(token)
cfile.close()