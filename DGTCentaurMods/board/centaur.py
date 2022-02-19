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

from subprocess import PIPE, Popen, check_output
import subprocess
import shlex
import configparser
import pathlib
import os, sys
import time
import json
import urllib.request

def get_lichess_api():
    global config
    lichess_api = config["lichess"]["api_token"]
    return lichess_api

def get_lichess_range():
    global config
    lichess_range = config["lichess"]["range"]
    return lichess_range

def get_sound():
    global config
    centaur_sound = config["sound"]["sound"]
    return centaur_sound

def set_lichess_api(key):
    global config
    global config_file
    config.set('lichess', 'api_token', key)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        configfile.close()

def set_lichess_range(newrange):
    global config
    global config_file
    config.set('lichess', 'range', newrange)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        configfile.close()

def set_sound(onoff):
    global config
    global config_file
    config.set('sound', 'sound', onoff)
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        configfile.close()

def rel_path():
    return str(pathlib.Path(__file__).parent.resolve()) + "/.."

def shell_run(rcmd):
    cmd = shlex.split(rcmd)
    executable = cmd[0]
    executable_options=cmd[1:]
    proc  = Popen(([executable] + executable_options), stdout=PIPE, stderr=PIPE)
    response = proc.communicate()
    response_stdout, response_stderr = response[0], response[1]
    if response_stderr:
        print(response_stderr)
        return -1
    else:
        print(response_stdout)
        return response_stdout


config_file = rel_path() + "/config/centaur.ini"
config = configparser.ConfigParser()
config.read(config_file)

# Import configs
try:
    lichess_api = config["lichess"]["api_token"]
except:
    lichess_api = ""
try:
    lichess_range = config["lichess"]["range"]
except:
    lichess_range = ""
try:
    centaur_sound = config["sound"]["sound"]
except:
    centaur_sound = "on"

class updateSystem:
    def __init__(self):
        self.status = self.getStatus()
        
        print('Update system status: ' + self.getStatus())
        print("Update source: ",config['update']['source'])
        print('Update channel: ' + self.getChannel())
        print('Policy: ' + self.getPolicy())
        #print('Installed version on the board: ' + self.getInstalledVersion())

        #Download update ingormation file
        self.update_source = config['update']['source']
        self.versions_file = '/tmp/versions.json'
        url = 'https://raw.githubusercontent.com/{}/master/build/config/versions.json'.format(self.update_source)
        try:
            print('Downloading update information...')
            urllib.request.urlretrieve(url,self.versions_file)
        except Exception as e:
            print('Cannot download update info: ', e)

        self.ver = json.load(open(self.versions_file))

            
    def getInstalledVersion(self):
        version = os.popen("dpkg -l | grep dgtcentaurmods | tr -s ' ' | cut -d' ' -f3").read().strip()
        return version

    def checkForUpdate(self):
        channel = self.getChannel()
        policy = self.getPolicy()
        print('Settings channel: '+channel)
        print('Settings policy: '+policy)
        try:
            curr_channel = self.getInstalledVersion().rsplit('.',1)[1].rsplit('-',1)[1]
        except:
            curr_channel = 'stable'
        print('Current channel: '+curr_channel)
        
        local_version = self.getInstalledVersion()
        local_major = self.getInstalledVersion().split('.')[0]
        local_minor = self.getInstalledVersion().split('.')[1]
        if curr_channel == 'stable':
            local_revision = self.getInstalledVersion().rsplit('.',1)[1]
        else:
            local_revision = self.getInstalledVersion().rsplit('.',1)[1].rsplit('-',1)[0]
        print('Local ver: '+local_version+'\nLocal major: '+local_major+'\nLocal minor: '+local_minor+'\nLocal revision: '+local_revision)
        
        self.update = self.ver[channel]['ota']
        update_major = self.update.split('.')[0]
        update_minor = self.update.rsplit('.')[1]
        if channel == 'stable':
            update_revision = self.update.rsplit('.',1)[1] 
        else:
            update_revision = self.update.rsplit('.',1)[1].rsplit('-',1)[0]
        print('Update ver: '+self.update+'\nUpdate major: '+update_major+'\nUpdate minor: '+update_minor+'\nUpdate revision: '+update_revision)
        
        #If local version is the same as update candidate, break
        if local_version == self.update:
            print('Versions are the same. No updates')
            return False
        
        if curr_channel != channel:
            print('Channel changed. Installing varsion {} at shutdown'.format(self.update))
            return True
        
        #Evaluate policies
        #On 'revision' install only if revision is newer
        if policy == 'revision':
            if local_major == update_major and local_minor == update_minor:
                if local_revision < update_revision:
                    return True
            else:
                print('Policy don\'t allow major updates.')
                return False

        #On 'always' just make sure this is an update to current installed version
        if policy == 'always':
            if local_major < update_major:
                return True 
            elif local_minor < update_minor:
                return True
            elif local_revision < update_revision:
                return True
            else:
                return False


    def downloadUpdate(self,update):
        download_url = 'https://github.com/{}/releases/download/v{}/dgtcentaurmods_armhf.deb'.format(self.update_source,update)
        print(download_url)
        try:
            urllib.request.urlretrieve(download_url,'/tmp/dgtcentaurmods_armhf.deb')
        except:
            return False
        return


    def enable(self):
        config.set('update','status','enabled')
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print('Autoupdate has been enabled')
        return
        

    def disable(self):
        config.set('update','status','disabled')
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print('Autoupdate has beed disabled.')
        return


    def setPolicy(self,policy):
        config.set('update','policy',policy)
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print('Policy set to: ' + policy)
        return


    def setChannel(self,channel):
        config.set('update','channel',channel)
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print('Update channel  has beed set to ',channel)
        return


    def getChannel(self):
        return config['update']['channel']


    def getStatus(self):
        return config['update']['status']


    def getPolicy(self):
        return config['update']['policy']


    def updateInstall(self):
        # Check for available update
        package = '/tmp/dgtcentaurmods_armhf.deb'
        update_helper = 'scripts/update.sh'
        print('Put the board in update mode')
        import shutil
        from DGTCentaurMods.display import epaper
        epaper.writeText(0, 'System is')
        epaper.writeText(1, 'updating...')
        shutil.copy(update_helper,'/tmp')
        print('About to execute the installer')
        time.sleep(3)
        os.system('. /tmp/update.sh')
        print('Stop DGTCM for update')
        time.sleep(6) # Wait for eink
        sys.exit()

    def main(self):
        # This function will run as a thread once, sometime after boot if updting is enabled.
        if not self.getStatus() == "disabled" and self.checkForUpdate():
            self.downloadUpdate(self.update)
            return
        print('Update not needed or disabled')
        return

