# DGTCentaurMods VERSION
### * ***This release only works on the second version of DGT centaur board*** *
You own a first verion of the board if your board has visible black circles on the fields. If you decide to install this software anyway, you can use the web interface to display in real time what should be on the screen. The web interface allows you to safely power off the board too.

## What's new in 1.3.2
- Adds a webdav based network drive (basic/experimental) with a PGN folder providing up to the latest 100 PGNs
- Allow update to latest release option in updates menu
- Update and display improvements
- Update from deb file in network share
- Fix various chess board outlines not aligned properly
- Fix epaper update when playing engines with analysis off
- Adds takebacks in UCI (engines) and 1v1Analysis
- Adds ignore computer move (and choose your own) in UCI (engines) and 1v1Analysis
- Logging to /home/pi/debug.log so available on network share
- Enable a shell on port 7777 from the menu (in case someone has ssh access problems)


## Installation
### Bootstrap install (new setup or upgrade)
You need to have a working Raspberry Pi inside the board with SSH enabled for this method.
This method will always install the LATEST release of DGTCentaurMods. In case you are looking to install a certain release, go to Manual installation.
#### Windows
- start Windows Power Shell
- execute: `iex (irm https://raw.githubusercontent.com/EdNekebno/DGTCentaurMods/master/tools/bootstrap/setup.ps1)`
- enter the ssh username and password
- enter a desired version or press ENTER to install the latest
- setup will start
- restart the board on finish to enable all features such as bluetooth, etc.
or try the new installation tool: https://github.com/EdNekebno/DGTCentaurMods/wiki/Creating-a-DGT-Centaur-Mods-SD-Card-on-Windows

#### Linux
- open a terminal window
- execute `ssh [username]@[ip_address] "curl -L https://raw.githubusercontent.com/EdNekebno/DGTCentaurMods/master/tools/bootstrap/setup.sh | bash"`
- enter the password to start the install
- restart the board on finish to enable all features such as bluetooth, etc.

#### Over SSH connection to the Centaur board
- `curl -L https://raw.githubusercontent.com/EdNekebno/DGTCentaurMods/master/tools/bootstrap/setup.sh | bash`
- restart the board on finish to enable all features such as bluetooth, etc.
- reboot the board in order to ensure all features are working
`sudo reboot`

### Manual install (new setup or upgrade)
You need a SSH connection to the board for this method.
1. Doenload to the board the deb installation file from the assets below. 
`wget  https://github.com/EdNekebno/DGTCentaurMods/releases/download/vVERSION/dgtcentaurmods_VERSION_armhf.deb`
2. Start the installation using:
`sudo apt install -y ./dgtcentaurmods_VERSION_armhf.deb`
4. Reboot the board: `sudo reboot`

### Using SD card self setup tool (new setup only)
This will create a new SD Card ready to use in you board. You must have a 2.4 Ghz WI-FI for this to work. It will self setup everything. Use the attached .pdf file to this release for instructions.
1. Download the card-setup-tool archive from the assets below.
2. Unzip the archive.
6. Start DGTCentaurModsInstaller.ps1 by right clicking and use Power shell. Follow on screen instructions.
7. Plug the card in the Raspberry Pi and wait for the setup to finish (about 10-25 minutes depending on the version of your RasPi W.

## Original centaur software
We recommend to use SD card setup tool to move the original centaur software to the new card. This is the safest way to ensure that the move is successfull. This needs to be done once in order to move the software, then you can user other install options.
Doing it manually is prone to errors unless you know what you're doing...

## Update system
If this is a new install, update system is disabled. You can enable that in the Settings -> Update opts, set status to Enabled.

## Notes
- DGT Centaur menu item will only show in the menu only if original software is on the board
- Lichess will activate once you put your lichess API token. Use board's settings or the web interface to set the token

## Known issues
- Bluetooth might be unstable
... you find others. Please create an issue in our project's GitHub page.

## Support
Get support on [Discord](https://discord.gg/zqgUGK2x49)

