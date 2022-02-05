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
        self.channel = config['update']['channel'] 
        token = config['update']['token']
        import apt
        import github
        self.cache = apt.Cache()
        gh = github.Github(token)
        
        #Get repo information and latest release object
        update_location = config["update"]["source"]
        try:
            self.repo = gh.get_repo(update_location)
        except:
            print('Cannot connect to update source.')
            return

        print('Update system status:')
        print('Status: ' + self.getStatus())
        print("Update source: ",update_location)
        print('Update channel: ' + self.getChannel())
        print('Policy: ' + self.getPolicy())
        print('Installed version on the board: ' + self.getInstalledVersion())

    def getInstalledVersion(self):
        version = self.cache['dgtcentaurmods'].versions.keys()
        return version[0]


    def checkForUpdate(self):
        # Check if there is an update for user selected channel
        local_version = self.getInstalledVersion()
        channel = self.getChannel() 
        
        # Get and itterate releases in the repo
        releases = self.repo.get_releases()
        # Return if no releases
        if releases.totalCount == 0:
            return False
        r = 0
        for item in releases:
            release_channel = ''
            if channel == 'stable' and not item.prerelease:
                print('Last release on ' + channel + ' channel is: ', item.title)
                self.latest_release = releases[r]
                return True
            for char in item.tag_name[1:]:
                if char.isalpha():
                    release_channel += char
            if release_channel == channel:
                print('Last release on ' + channel + ' channel is: ', item.title)
                self.latest_release = releases[r]
                return True
            r +=1


    def downloadUpdate(self):
        release_assets = self.latest_release.get_assets()
        for asset in release_assets:
            if asset.name == 'dgtcentaurmods_armhf.deb':
                download_url = asset.browser_download_url
                print(download_url)
        try:
            urllib.request.urlretrieve(download_url,'/tmp/dgtcentaurmods_armhf.deb')
        except:
            return False
        return True


    def checkPolicy(self):
        # Don't install major and minor updates.
        print('Checking update policy')
        if self.getPolicy() == "revision":
            local_majotminor = self.getInstalledVersion().rsplit('.',1)[0]
            latest_majotminor = self.latest_release.tag_name.rsplit('.',1)[0][1:]
            print(local_majotminor, latest_majotminor)
            if local_majotminor != latest_majotminor:
                print('This is a major update')
                print('Update not allowed. Policy is: ' + self.getPolicy())
                return
        else:
            self.downloadUpdate()


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
        os.system('./tmp/update.sh')
        print('Stop DGTCM for update')
        time.sleep(6) # Wait for eink
        sys.exit()

    def main(self):
        # This function will run as a thread once, sometime after boot if updting is enabled.
        if not self.getStatus() == "disabled" and self.checkForUpdate():
            self.checkPolicy()
            return
        print('Update not needed or disabled')
        return
