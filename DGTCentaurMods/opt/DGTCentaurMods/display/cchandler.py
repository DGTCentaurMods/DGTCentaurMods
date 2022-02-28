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