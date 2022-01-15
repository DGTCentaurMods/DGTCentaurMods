#!/usr/bin/python3

from DGTCentaurMods.board import board

import os
import time

#Make sure DGTM is stopped in case board is powered off by ssh
os.system("sudo systemctl stop DGTCentaurMods")
time.sleep(3)

print("Sending shutdown request to the controller")
board.shutdown()

