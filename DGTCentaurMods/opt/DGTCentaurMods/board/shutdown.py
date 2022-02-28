from DGTCentaurMods.board import board
from DGTCentaurMods.display import epaper
import os
import time

#LED
board.ledFromTo(7,7)

print("Sending shutdown request to the controller")
board.sleep()

