# What is this tool for?
This Tool allows you to create a SDcard for the Centaur with DGTCentaurMods installed and the original Centaur Software copied onto it in an almost automated way.

# How to use this tool

1. Right click the powershellscript DGTCentaurModsInstaller.ps1 and select run with powershell.

2. It will first download all required tools like 7zip, RaspBerryPI Imager and Win32DiskImager from their homepages.

3. Insert your original Centaur SDCard into your Card reader and create and image called centaur.img.

4. It will extract the Centaur folder from that image using 7zip and store it as centaur.tar.gz

5. It will use the Raspberry PI imager to create a SDcard with Bullseye. You will have to select the Bullseye lite image without desktop. In addition you should add your WIFI ID and password within the hidden menu by pressing "CNTRL" + "SHIFT"  + "x" at the same time.

6. As soon as Image is wriiten to the SDCard and you close the RaspberryPI imager program you can install the latest release by answering yes (Otherwise this menu allows you to add and install any debian package created by the build tools)

7. Select the Drive with boot drive of the SDcard.

8. The script will copy all files to the SDcard and you are ready to insert the SDcard to your Centaur Pi Zero W



