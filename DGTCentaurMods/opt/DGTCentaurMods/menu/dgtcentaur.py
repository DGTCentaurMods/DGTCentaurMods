# Menu item
# Name: DGT Centaur
# Description: start original DGT Centaur software

epaper.quickClear()
epaper.loadingScreen()
time.sleep(1)
board.pauseEvents()
self.statusbar.stop()
board.ser.close()
time.sleep(1)
os.chdir("/home/pi/centaur")
os.system("sudo ./centaur")
# Once started we cannot return to DGTCentaurMods, we can kill that
time.sleep(3)
os.system("sudo systemctl stop DGTCentaurMods.service")
sys.exit()
