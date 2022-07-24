# DGTCentaurMods Continous Integration System

## Docker image creation
This image runs a cron job  every 10 minutes by default. It builds a deb file in case `version` is updated in `DGTCentaurMods/DGTCentaurMods/DEBIAN` file on GitHub repo

### Build the image
Make sure you have a working Docker.
* Edit variables in the .ci.conf file
* If you want to change the interval of the cron job, edit the `root` file inside cron
* Build the image `sudo docker build <IMAGE_NAME> .`

### Starting the container
* `sudo docker run <IMAGE_ID>`

