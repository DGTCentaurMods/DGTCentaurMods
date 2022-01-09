#!/usr/bin/python3

from board import centaur

#Mass_storage device
class MSD:
    def enable():
        try:
            centaur.shell_run("sudo modprobe g_mass_storage file=../resources/MSD/usb.img stall=0")
        except:
            print("Cannot enable MSD")
        return

    def disable():
        try:
            centaur.shell_run("sudo rmmod g_mass_storage")
        except:
            print("Cannot remove MSD device")
        return

#Ethernet over USB device
class ether:
    def enable():
        try:
            centaur.shell_run("sudo modprobe g_ether")
        except:
            print("Cannot enable Ethernet Device. Unknown error.")
        return

    def disable():
        try:
            centaur.shell_run("sudo rmmod g_ether")
        except:
            pass
        return
