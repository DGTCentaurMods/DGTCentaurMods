#!/usr/bin/bash

IF="wlan0"

BACKUP_DIR="/home/pi/backup"
WPA_BACKUP_CONF="$BACKUP_DIR/wpa_supplicant.conf"
WPA_CONF="/etc/wpa_supplicant/wpa_supplicant.conf"
WPA_DIR="/etc/wpa_supplicant/"

echo $BACKUP_DIR
echo $WPA_CONF

if [ $1 = "backup" ]
then
    if [ -e $WPA_CONF ]
    then
        echo "Baking up wpa_supplicant.conf"
        if [ ! -d $BACKUP_DIR ]
        then
            echo "Creating backup directory."
            mkdir -p $BACKUP_DIR
            echo "Backing up wpa_supplicant.conf"
            cp $WPA_CONF $BACKUP_DIR
            echo "Done."
            exit 0
        else
            cp $WPA_CONF $BACKUP_DIR
            exit 0
        fi
    else
        exit 1
    fi
fi

if [ $1 = "restore" ]
then
    if [ -e $WPA_BACKUP_CONF ]
    then
        echo "Restoring wpa_supplicant..."
        cp $WPA_BACKUP_CONF $WPA_DIR
        wpa_cli -i $IF reconfigure
        wpa_cli -i $IF reconnect

        dhcpcd $IF reload

        exit 0
    else
        exit 1
    fi
    exit 0
fi

