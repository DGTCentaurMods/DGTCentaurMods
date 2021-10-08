import bluetooth, subprocess
# This only works on android/PC - presumably because only bluetoothclassic is working at the moment, no BLE
status = subprocess.call("echo -e \"yes\" | bt-agent --capability=NoInputNoOutput -p /etc/bluetooth/pin.conf &",shell=True)
