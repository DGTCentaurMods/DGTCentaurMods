""" Provides Display Communication Services """

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

from ctypes import *
import pathlib

class epaperDriver(object):
    """ Class representing epaperDriver Communications """

    instance = None    
    driverFunc = None       

    def __new__(cls):
        if cls.instance is None:            
            cls.instance = super(epaperDriver, cls).__new__(cls)
            cls.driverFunc = CDLL(str(pathlib.Path(__file__).parent.resolve()) + "/../display/epaperDriver.so")
            cls.driverFunc.openDisplay()
            print("Opened new driver\n")
        return cls.instance
