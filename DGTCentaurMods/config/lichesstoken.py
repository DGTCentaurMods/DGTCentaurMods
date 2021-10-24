# Quick temporary script to set up the lichess token until we have a db method
#

from DGTCentaurMods.board import board
from DGTCentaurMods.board import centaur
import os
import time
import sys
import re
import pathlib

board.initScreen()
time.sleep(2)

# Get the token
token = board.getText("API Token")

if token == "":
	sys.exit()

centaur.set_lichess_api(token)
