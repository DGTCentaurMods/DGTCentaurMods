#!/usr/bin/python3

# OTG support classes.
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

from board import centaur

#Mass_storage device
class MSD:
    def enable():
        try:
            centaur.shell_run("sudo modprobe g_mass_storage file=../resources/MSD/usb.img stall=0")
        except:
            print("Cannot enable MSD")
        return

    def disable():
        try:
            centaur.shell_run("sudo rmmod g_mass_storage")
        except:
            print("Cannot remove MSD device")
        return

#Ethernet over USB device
class ether:
    def enable():
        try:
            centaur.shell_run("sudo modprobe g_ether")
        except:
            print("Cannot enable Ethernet Device. Unknown error.")
        return

    def disable():
        try:
            centaur.shell_run("sudo rmmod g_ether")
        except:
            pass
        return
