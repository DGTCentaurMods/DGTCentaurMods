import bluetooth, subprocess
status = subprocess.call("echo -e \"yes\" | bt-agent --capability=NoInputNoOutput -p /etc/bluetooth/pin.conf &",shell=True)
