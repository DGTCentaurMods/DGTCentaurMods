# This file contains functions needed
# for the network adapter to connect to wifi
# using WPS.
#
# (c)2021 wormstein

from subprocess import PIPE, Popen, check_output
import subprocess
import re
import time
import os
import shlex
import logging

def run_program(rcmd):
    cmd = shlex.split(rcmd)
    executable = cmd[0]
    executable_options=cmd[1:]
    proc  = Popen(([executable] + executable_options), stdout=PIPE, stderr=PIPE)
    response = proc.communicate()
    response_stdout, response_stderr = response[0], response[1]
    return response_stdout


def check_network():
    ret = subprocess.check_output(["ifconfig", "wlan0"]).decode("utf-8")
    reg = re.search("inet (\d+\.\d+\.\d+\.\d+)", ret)
    if reg is None:
        return False
    else:
        return reg.group(1)

def detect_wps(i=0):
    while i < 10:
        subprocess.check_output(["wpa_cli", "-i", "wlan0", "scan"])
        time.sleep(1)
        wpa = subprocess.check_output(["wpa_cli", "-i", "wlan0", "scan_results"]).decode("UTF-8")
        network = re.search("(([\da-f]{2}:){5}[\da-f]{2})(.*?)\[WPS-PBC\]", wpa)
        if not (network is None):
            if network.group(1):
                return network.group(1)
        time.sleep(3)
        i += 1

def connect_wps(network=""):
    is_network = check_network()
    print("Press WPS button now")
    print("Waiting to connect...")
    run_program("wpa_cli -i wlan0 wps_pbc " + network)
    time.sleep(60)
    is_network = check_network()
    # Wait dhcp
    time.sleep(10)
    # Sometine network is disabled
    run_program("wpa_cli -i wlan0 enable_network 0")
    if is_network:
        print("Network is up!")
        return True
    else:
        print("Network is down")

def disconnect_all():
    run_program("wpa_cli -i wlan0 remove_network all")
    run_program("wpa_cli -i wlan0 save_config")

