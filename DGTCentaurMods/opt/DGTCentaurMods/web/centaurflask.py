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

#from DGTCentaurMods.display import epaper
from subprocess import PIPE, Popen, check_output
from DGTCentaurMods.board.settings import Settings
import subprocess
import shlex
import pathlib
import os, sys
import time
import json
import urllib.request

def get_lichess_api():
    return Settings.read('lichess','api_token','')        

def get_lichess_range():
    return Settings.read('lichess','range','0-3000')

def get_menuEngines():
    return Settings.read('menu','showEngines', 'checked')

def get_menuHandBrain():
    return Settings.read('menu','showHandBrain', 'checked')

def get_menu1v1Analysis():
    return Settings.read('menu','show1v1Analysis','checked')

def get_menuEmulateEB():
    return Settings.read('menu','showEmulateEB','checked')

def get_menuCast():
    return Settings.read('menu','showCast','checked')

def get_menuSettings():
    return Settings.read('menu','showSettings','checked')

def get_menuAbout():
    return Settings.read('menu','showAbout','checked')

def get_sound():
    return Settings.read('sound','sound','on')

def set_lichess_api(key):
    return Settings.write('lichess','api_token', key)

def set_lichess_range(newrange):
    return Settings.write('lichess','range',newrange)

def set_sound(onoff):
    return Settings.write('sound','sound','on')

def set_menuEngines(val):
    return Settings.write('menu','showEngines',val)
        
def set_menuHandBrain(val):
    return Settings.write('menu','showHandBrain',val)

def set_menu1v1Analysis(val):
    return Settings.write('menu','show1v1Analysis',val)  
        
def set_menuEmulateEB(val):
    return Settings.write('menu','showEmulateEB',val)
        
def set_menuCast(val):
    return Settings.write('menu','showCast',val)
        
def set_menuSettings(val):
    return Settings.write('menu','showSettings',val)
        
def set_menuAbout(val):
    return Settings.write('menu','showAbout',val)