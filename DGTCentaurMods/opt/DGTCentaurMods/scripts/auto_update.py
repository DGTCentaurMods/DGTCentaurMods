# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
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
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from pathlib import Path
import os, glob, time

HOME_DIRECTORY = str(Path.home())
MAIN_ID = "DGTCentaurMods"

deb_files = glob.glob(f"{HOME_DIRECTORY}/{MAIN_ID}*.deb")

if len(deb_files)>0:
    print(f"One {MAIN_ID} package file has been found!")
    filename = deb_files[0]
    print(f"Installing '{filename}'...")

    time.sleep(5)

    print("DPKG configuration...")
    os.system("sudo sudo dpkg --configure -a")

    print("Uninstalling current version...")
    os.system("sudo apt remove -y dgtcentaurmods")

    print("Installing package...")
    os.system(f"sudo apt install -y {filename}")

    print("Cleaning deb file...")
    os.system(f"sudo rm -f {HOME_DIRECTORY}/*.deb >/dev/null 2>&1")

    print("Restarting services...")
    os.system('sudo systemctl start "DGTCentaurModsWeb.service"')
    os.system('sudo systemctl start "DGTCentaurMods.service"')
else:
    print(f"No pending {MAIN_ID} update has been found...")

exit()