# This file contains functions needed
# for the network adapter to connect to wifi
# using WPS.
#
# (c)2021 wormstein
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
import re
import time
import os
import shlex

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

def check_network():
    ret = shell_run("ifconfig wlan0").decode("utf-8")
    reg = re.search("inet (\d+\.\d+\.\d+\.\d+)", ret)
    if reg is None:
        return False
    else:
        return reg.group(1)

def wps_detect(i=0):
    """
    In case you need to extract MAC address of the router with WPS button
    pressed to use with wps_connect()
    """
    while i < 10:
        shell_run("wpa_cli -i wlan0 scan")
        time.sleep(1)
        wpa = shell_run("wpa_cli -i wlan0 scan_results").decode("UTF-8")
        network = re.search("(([\da-f]{2}:){5}[\da-f]{2})(.*?)\[WPS-PBC\]", wpa)
        if not (network is None):
            if network.group(1):
                return network.group(1)
        time.sleep(3)
        i += 1

def wps_connect(network=""):
    is_network = check_network()
    print("Press WPS button now")
    print("Waiting to connect...")
    shell_run("wpa_cli -i wlan0 wps_pbc " + network)
    time.sleep(60)
    is_network = check_network()
    # Sometine network is disabled
    shell_run("wpa_cli -i wlan0 enable_network 0")
    # Wait dhcp
    time.sleep(10)
    if is_network:
        print("Network is up!")
        return True
    else:
        print("Network is down")

def wps_disconnect_all():
    shell_run("wpa_cli -i wlan0 remove_network all")
    shell_run("wpa_cli -i wlan0 save_config")

