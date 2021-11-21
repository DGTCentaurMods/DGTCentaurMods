# Connect to a Wifi Network
#

from DGTCentaurMods.board import board
import os
import time
import sys
import re

board.initScreen()
time.sleep(2)

command = """iwlist wlan0 scan | grep -i 'essid:"' | cut -c28-500"""
result = os.popen(command)
result = list(result)
networks = {}
for i in range(0,len(result)):
	result[i] = result[i].replace("\n","")
	result[i] = result[i].replace("\"","")
	result[i] = result[i].replace("\\x00",".")
	result[i] = result[i].replace("\\\\","\\")
	result[i] = result[i].replace("\\xE2",'\xE2')
	result[i] = result[i].replace("\\x80",'\x80')
	result[i] = result[i].replace("\\x99",'\x99')
	networks[result[i]] = result[i]

print(networks)
answer = board.doMenu(networks,1)

print(answer)

if answer == "BACK":
	sys.exit()

#board.initScreen()
#time.sleep(2)
board.epd.init()

# If the answer is not "BACK" then answer contains our SSID
# Now we need to get the password
password = board.getText("Wifi Password")

if password == "":
	sys.exit()

# Add an SSID
cmd = """sudo sh -c \"wpa_passphrase '""" + answer + """' '""" + password + """'\""""
res = os.popen(cmd)
result = list(res)
section = ""
for i in range(0,len(result)):
	section = section + result[i]
print(section)
if section.find("ssid") != -1:
	wpas = open('/etc/wpa_supplicant/wpa_supplicant.conf','r')
	curconf = wpas.read()
	wpas.close()
	print(curconf)
	if curconf.find(answer) != -1:
		# SSID is already in file
		newtext = re.sub('network={[^\}]+?ssid=\"' + answer + '\"[^\}]+?\}\n','',curconf,re.DOTALL)
		print(newtext)
		wpas = open('/etc/wpa_supplicant/wpa_supplicant.conf','w')
		wpas.write(newtext)
		wpas.close()
	# Success - append it to wpa_supplicant
	wpas = open('/etc/wpa_supplicant/wpa_supplicant.conf','a')
	wpas.write(section)
	wpas.close()
	os.system("sudo wpa_cli -i wlan0 reconfigure")

