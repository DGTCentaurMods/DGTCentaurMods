from DGTCentaurMods.board import network
import time
import pathlib
import os
import sys
import pychromecast
from random import random

cn = sys.argv[1]

while True:
    chromecasts = pychromecast.get_chromecasts()
    ccid = -1
    id = 0

    for cc in chromecasts[0]:
        if cn == cc.device.friendly_name:
            ccid = id
        id = id + 1

    if ccid == -1:
        sys.exit()

    print(chromecasts[0][ccid].status)
    chromecasts[0][ccid].wait()
    mc = chromecasts[0][ccid].media_controller
    IP = network.check_network()
    mc.play_media("http://" + IP + ":5000/video?" + str(random()), 'image/jpeg',stream_type='LIVE')
    mc.block_until_active()
    mc.play()

    while chromecasts[0][ccid].status.display_name == 'Default Media Receiver':
        time.sleep(0.5)

    print("stopped playing")