# Menu item
# Name: about
# Description: display about information

import os,pathlib
from PIL import Image

version = os.popen("dpkg -l | grep dgtcentaurmods | tr -s ' ' | cut -d' ' -f3").read()
epaper.writeText(1,'Get support:')
epaper.writeText(9,'DGTCentaur')
epaper.writeText(10,'      Mods')
epaper.writeText(11,'Ver:' + version)
qr = Image.open(str(pathlib.Path(__file__).parent.resolve()) +"/../resources/qr-support.png")
qr = qr.resize((128,128))
epaper.epaperbuffer.paste(qr,(0,42))

epaper.drawImagePartial(0,0,epaper.epaperbuffer.crop((0,0,128,292)))

