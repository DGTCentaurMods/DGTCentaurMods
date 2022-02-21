from DGTCentaurMods.board import board
from DGTCentaurMods.display import epaper
import os
import time

#Beep and LED
board.beep(board.SOUND_POWER_OFF)
board.ledFromTo(7,7)

print("Sending shutdown request to the controller")
board.sleep()

