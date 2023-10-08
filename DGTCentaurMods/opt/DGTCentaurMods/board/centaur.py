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

from DGTCentaurMods.display import epaper
from DGTCentaurMods.board.settings import Settings
from subprocess import PIPE, Popen, check_output
import subprocess
import shlex
import pathlib
import os, sys
import time
import json
import urllib.request
import logging

try:
    logging.basicConfig(level=logging.DEBUG, filename="/home/pi/debug.log",filemode="w")
except:
    logging.basicConfig(level=logging.DEBUG)

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

def dgtcm_path():
    return str(pathlib.Path(__file__).parent.resolve()) + "/.."

def shell_run(rcmd):
    cmd = shlex.split(rcmd)
    executable = cmd[0]
    executable_options=cmd[1:]
    proc  = Popen(([executable] + executable_options), stdout=PIPE, stderr=PIPE)
    response = proc.communicate()
    response_stdout, response_stderr = response[0], response[1]
    if response_stderr:
        logging.debug(response_stderr)
        return -1
    else:
        logging.debug(response_stdout)
        return response_stdout


config = Settings.get_config()
lichess_api = Settings.read('lichess','api_token','')
lichess_range = Settings.read('lichess','range','0-3000')
centaur_sound = Settings.read('sound','sound','on')

class UpdateSystem:
    def __init__(self):
        self.status = self.getStatus()
        

    def info(self):
        logging.debug('Update system status: ' + self.getStatus())
        logging.debug("Update source: ", Settings.read('update', 'source', 'EdNekebno/DGTCentaurMods'))
        logging.debug('Update channel: ' + self.getChannel())
        logging.debug('Policy: ' + self.getPolicy())

    def getInstalledVersion(self):
        version = os.popen("dpkg -l | grep dgtcentaurmods | tr -s ' ' | cut -d' ' -f3").read().strip()
        return version

    def checkForUpdate(self):
        channel = self.getChannel()
        policy = self.getPolicy()
        logging.debug('Settings channel: '+channel)
        logging.debug('Settings policy: '+policy)
        try:
            curr_channel = self.getInstalledVersion().rsplit('.',1)[1].rsplit('-',1)[1]
        except:
            curr_channel = 'stable'
        logging.debug('Current channel: '+curr_channel)
        
        local_version = self.getInstalledVersion()
        local_major = self.getInstalledVersion().split('.')[0]
        local_minor = self.getInstalledVersion().split('.')[1]
        try:
            local_minor = self.getInstalledVersion().split('.')[1]
        except:
            local_minor = '0'

        if curr_channel == 'stable':
            try:
                local_revision = self.getInstalledVersion().split('.')[2]
            except:
                local_revision = '0'
        else:
            local_revision = self.getInstalledVersion().rsplit('.',1)[1].rsplit('-',1)[0]
        #Dpkg is skipping 0 if last in version number. e.g: 1.1.0 will be 1.1
        #We need to rebuild the version
        local_version = '{}.{}.{}'.format(local_major,local_minor,local_revision)
        logging.debug('Local ver: '+local_version+'\nLocal major: '+local_major+'\nLocal minor: '+local_minor+'\nLocal revision: '+local_revision)
        
        self.update = self.ver[channel]['ota']
        #No OTA, no update
        if self.update == 'None':
            return False
        update_major = self.update.split('.')[0]
        update_minor = self.update.rsplit('.')[1]
        if channel == 'stable':
            update_revision = self.update.rsplit('.',1)[1] 
        else:
            update_revision = self.update.rsplit('.',1)[1].rsplit('-',1)[0]
        logging.debug('Update ver: '+self.update+'\nUpdate major: '+update_major+'\nUpdate minor: '+update_minor+'\nUpdate revision: '+update_revision)
        
        #If local version is the same as update candidate, break
        if local_version == self.update:
            logging.debug('Versions are the same. No updates')
            return False
        
        #If user decides to switch channel, he will trigger a full reinstall
        if curr_channel != channel:
            logging.debug('Channel changed. Installing varsion {} at shutdown'.format(self.update))
            return True
        
        #Evaluate policies
        #On 'revision' install only if revision is newer
        if policy == 'revision':
            if local_major == update_major and local_minor == update_minor:
                if local_revision < update_revision:
                    return True
            else:
                logging.debug('Policy don\'t allow major updates.')
                return False

        #On 'always' just make sure this is an update to current installed version
        if policy == 'always':
            vallocal = int(local_revision) + (int(local_minor) * 100) + (int(local_major) * 10000)
            valupdate = int(update_revision) + (int(update_minor) * 100) + (int(update_major) * 10000)
            if valupdate > vallocal:
                return True
            else:
                return False


    def downloadUpdate(self,update):
        download_url = 'https://github.com/{}/releases/download/v{}/dgtcentaurmods_{}_armhf.deb'.format(self.update_source,update,update)
        logging.debug(download_url)
        try:
            urllib.request.urlretrieve(download_url,'/tmp/dgtcentaurmods_armhf.deb')
        except:
            return False
        return


    def enable(self):
        Settings.write('update','status','enabled')
        logging.debug('Autoupdate has been enabled')
        return
        

    def disable(self):
        Settings.write('update','status','disable')        
        logging.debug('Autoupdate has beed disabled.')
        return


    def setPolicy(self,policy):
        Settings.write('update','policy',policy)        
        logging.debug('Policy set to: ' + policy)
        return


    def setChannel(self,channel):
        Settings.write('update','channel',channel)        
        logging.debug('Update channel  has beed set to ',channel)
        return


    def getChannel(self):        
        return Settings.read('update', 'channel', 'stable')        


    def getStatus(self):
        return Settings.read('update', 'status', 'disabled')        


    def getPolicy(self):
        return Settings.read('update', 'policy', 'always')        


    def updateInstall(self):
        # Check for available update
        package = '/tmp/dgtcentaurmods_armhf.deb'
        logging.debug('Put the board in update mode')
        import shutil

        epaper.writeText(3, '    System will')
        epaper.writeText(4, '       update')
        shutil.copy('update/update.py','/tmp')
        shutil.copytree('update/lib','/tmp/lib')
        logging.debug('Keep the info on the screen')
        time.sleep(5)
        subprocess.Popen('cd /tmp; python /tmp/update.py', shell=True)
        sys.exit()


    def main(self):
        #Download update ingormation file
        self.update_source = Settings.read('update','source','EdNekebno/DGTCentaurMods')
        logging.debug('Downloading update information...')
        url = 'https://raw.githubusercontent.com/{}/master/DGTCentaurMods/DEBIAN/versions'.format(self.update_source)
        try:
            with urllib.request.urlopen(url) as versions:
                self.ver = json.loads(versions.read().decode())
        except Exception as e:
            logging.debug('!! Cannot download update info: ', e)
            pass

        # This function will run as a thread once, sometime after boot if updting is enabled.
        if not self.getStatus() == "disabled" and self.checkForUpdate():
            self.downloadUpdate(self.update)
            return
        logging.debug('Update not needed or disabled')
        return
