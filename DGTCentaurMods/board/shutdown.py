from DGTCentaurMods.board import board
from DGTCentaurMods.display import epaper

import os
import time

#Beep
board.beep(board.SOUND_POWER_OFF)

#Make sure DGTM is stopped in case board is powered off by ssh
os.system("sudo systemctl stop DGTCentaurMods")

epaper.initEpaper()
time.sleep(6)
epaper.stopEpaper()

print("Sending shutdown request to the controller")
board.shutdown()

