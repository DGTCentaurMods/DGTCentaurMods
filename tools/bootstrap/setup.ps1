# Bootstrap installer for DGTCentaurMods using Windows PowerShell
#

$releaseVersion = '1.1.3'
$username = "pi"
$hostname = 'dgtcentaur.local'
$releaseFileName = -join ("dgtcentaurmods_" , $releaseVersion , "_armhf.deb" )
$releaseURL = -join ("https://github.com/EdNekebno/DGTCentaurMods/releases/download/v", $releaseVersion , "/" , $releaseFileName )

$raspiUser = Read-Host -Prompt "Enter the username for your Centaur board ($username)"
$raspiUser = ($username,$raspiUser)[[bool]$raspiUser]

$raspiIP = Read-Host -Prompt "Enter the IP/hostname of your Centaur board ($hostname)"
$raspiIP = ($hostname,$raspiIP)[[bool]$raspiIP]

ssh $raspiUser@$raspiIP "
wget -q $releaseURL
sudo apt install -y ./$releaseFileName
rm $releaseFileName
echo -e '\nRebooting'
sudo reboot"

Read-Host -Prompt "Press ENTER to exit.... "
