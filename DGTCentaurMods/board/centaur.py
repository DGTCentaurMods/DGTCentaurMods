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
import os

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
        import apt
        import github
        self.cache = apt.Cache()
        gh = github.Github()
        
        #Get repo information and latest release object
        update_location = config["update"]["source"]
        print("Update location: ",update_location)
        repo = gh.get_repo(update_location)
        self.releases = repo.get_releases()
        self.last_release = self.releases[0]
        
        #Get latest release ID and version
        self.id,self.version = self.last_release.id, self.last_release.tag_name
        print("Latest release ID: ",self.id)
        print("Latest release version: ",self.version)


    def getInstalledVersion(self):
        version = self.cache['dgtcentaurmods'].versions.keys()
        print(version[0])
        return version[0]


    def checkForUpdate(self):
        local = self.getInstalledVersion()
        latest = self.version
        if local != latest:
            # TODO:
            # Compare version by major, minor and revicion numbers. On revisions we just check if name differs while major and minor is the same. Maybe we can compare release dates.
            # Check user settings and decide if he wants just a revicion update.
            #If normal update is enabled, get the package downloaded in the background
            print('Update is available.')
            self.downloadUpdate()
            return True
        else:
            print('System is up to date')
            return False


    def downloadUpdate(self):
        last_release_assets = self.last_release.get_assets()
        for asset in last_release_assets:
            if asset.name == 'dgtcentaurmods_armhf.deb':
                download_url = asset.browser_download_url
                print(download_url)
        # TODO:
        # Download in the background and set installating at shutdown


    def enable(self):
        config.set('update','autoupdate','1')
        return
        

    def disable(self):
        config.set('update','autoupdate','0')
        return


