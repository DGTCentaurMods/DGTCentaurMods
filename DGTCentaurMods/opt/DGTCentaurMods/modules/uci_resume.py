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

from DGTCentaurMods.classes.CentaurConfig import CentaurConfig

import importlib, shlex

def main():

    last_uci = CentaurConfig.get_last_uci_command()

    if last_uci == "1vs1_module":
        uci_module = importlib.import_module(name=last_uci, package="DGTCentaurMods.game")
        uci_module.main()
    else:
        uci_module = importlib.import_module(name="uci_module", package="DGTCentaurMods.game")
        # We unpack the last_uci args
        uci_module.main(*shlex.split(last_uci))

if __name__ == '__main__':
    main()