""" Provides the classes and components for the ui interface """

# DGT Centaur display control functions
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

class AssetManager():
    """ Class representing epaperDriver Communications """

    @staticmethod
    def get_resource_path(resource_file):
        """ Return resource path from the resources folder or /home/pi/resources """

        if resource_file.find("..") >= 0:
            return ""

        if os.path.exists("/home/pi/resources/" + resource_file):
            return "/home/pi/resources/" + resource_file
        else:
            return "/opt/DGTCentaurMods/resources/" + resource_file
        