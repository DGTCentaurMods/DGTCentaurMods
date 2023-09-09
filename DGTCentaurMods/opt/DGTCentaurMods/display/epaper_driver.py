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
#

from ctypes import *
from PIL import Image
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
        return cls.instance
    
    def getbuffer(self, image):
        """ Converts a PIL image to a byte buffer """
        buf = [0xFF] * (int(128 / 8) * 296)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        if(imwidth == 128 and imheight == 296):
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        buf[int((x + y * 128) / 8)
                            ] &= ~(0x80 >> (x % 8))
        elif(imwidth == 296 and imheight == 128):
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = 296 - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy * 128) / 8)
                            ] &= ~(0x80 >> (y % 8))
        else:        
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        buf[int((x + y * 128) / 8)
                        ] &= ~(0x80 >> (x % 8))                        
        return bytes(buf)
    
    def init(self):
        """ Initialise the epaper display """
        self.driverFunc.init()
        
    def reset(self):
        """ Reset the epaper display """
        self.driverFunc.reset()
        
    def clear(self):
        """ Clear the epaper display """
        self.driverFunc.clear()
        
    def display(self, bitmap):
        """ Display the passed black and white bitmap image """
        self.driverFunc.display(self.getbuffer(bitmap))
        
    def DisplayPartial(self, bitmap):
        """ Display the passed black and white bitmap image in Partial mode """
        self.driverFunc.displayPartial(self.getbuffer(bitmap))
    
    def DisplayRegion(self, y0, y1, bitmap):
        """ Display the passed black and white part bitmap image in Partial mode """
        self.driverFunc.displayRegion(y0, y1, self.getbuffer(bitmap))
        
    def sleepDisplay(self):
        """ Puts the epaper display in sleep mode """
        self.driverFunc.sleepDisplay()
        
    def powerOffDisplay(self):
        """ Powers down the epaper display """
        self.driverFunc.powerOffDisplay()        