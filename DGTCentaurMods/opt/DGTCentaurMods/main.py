#Get all you need here
from DGTCentaurMods.board import *
from DGTCentaurMods.display import epaper
import time
import threading

menu = centaur.MenuSystem()
statusbar = epaper.statusBar()
update = centaur.UpdateSystem()

update.info()

# Start the display,turn off LEDs
epaper.initEpaper()
board.ledsOff()

# Start the menu
menu.main()

# Will check fot updates soon
threading.Timer(300,update.main).start()

#Demonize
while True:
    time.sleep(0.08)

