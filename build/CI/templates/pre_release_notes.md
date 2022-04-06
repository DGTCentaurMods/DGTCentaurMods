# DGTCentaurMods VERSION - Pre-release
### * ***This release only works on the second version of DGT centaur board*** *
You own a first verion of the board if your board has visible black circles on the fields. If you decide to install this software anyway, you can use the web interface to display in real time what should be on the screen. The web interface allows you to safely power off the board too.

This is a pre-release version of our software. This means it will never be pushed as OTA update, is not the default version in our bootstrap install and it is not a stable release. You might face issues  when using it especially with the new fetaures or bug fixes for this pre-releas. If you do find new bugs, we encourage you to (re)open an issue on our GitHub project page.

## Installation
This is a pre-release and the only option to install it is to download the deb package and perform a manual install. You can use the card-setup-tool and specify the version number when the tool prompts for it.
### Manual install (new setup or upgrade)
You need a SSH connection to the board for this method.
1. Doenload to the board the deb installation file from the assets below. 
`wget  https://github.com/EdNekebno/DGTCentaurMods/releases/download/vVERSION/dgtcentaurmods_VERSION_armhf.deb`
2. Start the installation using:
`sudo apt install -y ./dgtcentaurmods_VERSION_armhf.deb`
4. Reboot the board: `sudo reboot`

### Using SD card self setup tool (new setup only)
This will create a new SD Card ready to use in you board. It will self setup everything. Use the attached .pdf file to this release for instructions.
1. Download the card-setup-tool archive from the assets below.
2. Unzip the archive.
6. Start DGTCentaurModsInstaller.ps1 by right clicking and use Power shell. Follow on screen instructions. Specify the version VERSION when asked.
7. Plug the card in the Raspberry Pi and wait for the setup to finish (about 10-25 minutes depending on the version of your RasPi W.

## Original centaur software
We recommend to use SD card setup tool to move the original centaur software to the new card. This is the safest way to ensure that the move is successfull. This needs to be done once in order to move the software, then you can user other install options.
Doing it manually is prone to errors unless you know what you're doing...

## Update system
If this is a new install, update system is disabled. You can enable that in the Settings -> Update opts, set status to Enabled.

## Support
Get support on [Discord](https://discord.gg/zqgUGK2x49)

