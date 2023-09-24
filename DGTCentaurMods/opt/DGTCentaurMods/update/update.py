#!/usr/bin/python
# Display progess of DGTCentaurMods installation on first boot
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

import os
from lib import *
import os, time
import threading
import subprocess

global animate
global progress

epaper.initEpaper(1)
epaper.clearScreen()

sb = epaper.statusBar()
sb.start()
sb.print()

def status():
    global animate
    global progress
    animate = True
    while animate:
        for a in ['/','-','\\','|']:
            epaper.writeText(1,progress + "[" + a + "]")
            time.sleep(1)


progress = 'Updating OS    '
msg = threading.Thread(target=status,args=())
msg.start()
time.sleep(0.5)
epaper.writeText(3,"[1/2] Updating")
epaper.writeText(4,"    Raspbian")
#os.system("sudo apt update")
cmd = ["sudo", "apt", "update"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
try:
    for line in proc.stdout:
        epaper.writeText(10,str(line.decode()) + "                    ")
        logging.debug(str(line))        
except:    
    pass
cmd = ["sudo", "apt", "full-upgrade", "-y"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
try:
    for line in proc.stdout:
        epaper.writeText(10,str(line.decode()) + "                    ")
        logging.debug(str(line))        
except:    
    pass
#os.system("sudo apt full-upgrade -y")

progress = 'Updating       '
epaper.writeText(5,"[2/2] Updating")
epaper.writeText(6,"    DGTCM")
cmd = ["sudo", "apt", "install", "-y", "/tmp/dgtcentaurmods_armhf.deb"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
try:
    for line in proc.stdout:
        epaper.writeText(10,str(line.decode()) + "                    ")
        logging.debug(str(line))        
except:    
    pass
#os.system("sudo apt install -y /tmp/dgtcentaurmods_armhf.deb")

animate = False
sb.stop()
time.sleep(3)
epaper.clearScreen()
time.sleep(1)
print('Setup done')

epaper.writeText(3,'     Shutting')
epaper.writeText(4,'       down')
time.sleep(5)
epaper.initEpaper()
epaper.clearScreen()
epaper.stopEpaper()
os.system("sudo systemctl start stopDGTController.service")
