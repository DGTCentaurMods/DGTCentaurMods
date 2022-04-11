# Bootstrap installer for DGTCentaurMods using Windows PowerShell
#

$currentReleaseVersion = '1.1.7'
write-Host "Latest release version is $currentReleaseVersion"
Write-Host "If you want to install another release, input the version number below"
$releaseVersion = Read-Host -Prompt "Enter the version number ($currentReleaseVersion)"
$releaseVersion = ($currentReleaseVersion,$releaseVersion)[[bool]$releaseVersion]

$username = "pi"
$hostname = 'dgtcentaur.local'
$releaseFileName = -join ("dgtcentaurmods_" , $releaseVersion , "_armhf.deb" )
$releaseURL = -join ("https://github.com/EdNekebno/DGTCentaurMods/releases/download/v", $releaseVersion , "/" , $releaseFileName )

$raspiUser = Read-Host -Prompt "Enter the username for your Centaur board ($username)"
$raspiUser = ($username,$raspiUser)[[bool]$raspiUser]

$raspiIP = Read-Host -Prompt "Enter the IP/hostname of your Centaur board ($hostname)"
$raspiIP = ($hostname,$raspiIP)[[bool]$raspiIP]

ssh $raspiUser@$raspiIP "
echo -e 'Downloading DGTCentaurMods $releaseVersion'
wget -q $releaseURL
sudo apt install -y ./$releaseFileName
rm $releaseFileName
echo -e '\nRebooting'
sudo reboot"

Read-Host -Prompt "Press ENTER to exit.... "
