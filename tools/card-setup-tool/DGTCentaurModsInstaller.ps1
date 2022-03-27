Import-Module BitsTransfer
#
#Tool for Windows Powershell to facilitate creation of an SD Card
#containing Raspbian OS and that will auto setup DGTCentaurMods.
#
#This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.


$currentReleaseVersion = '1.1.2'
$dev = '0'
$SleepTime = 3

write-Host "Latest release version is $currentReleaseVersion"
Write-Host "If you want to install another release, input the version number below"
$releaseVersion = Read-Host -Prompt "Enter the version number ($currentReleaseVersion)"
$releaseVersion = ($currentReleaseVersion,$releaseVersion)[[bool]$releaseVersion]

$releaseFileName = -join ("dgtcentaurmods_" , $releaseVersion , "_armhf.deb" )
$releaseURL = -join ("https://github.com/EdNekebno/DGTCentaurMods/releases/download/v", $releaseVersion , "/" , $releaseFileName )

function retrieveFiles($URL, $fileName, $OutPutFolder) {
    $OutPutFolder = "$PSScriptRoot\$OutPutFolder"
    #   "Test to see if folder [$OutPutFolder]  exists"
    if (Test-Path -Path $OutPutFolder) {
        "Path $OutPutFolder exists!"
    }
    else {
        $start_time = Get-Date
        if (Test-Path -Path "$PSScriptRoot\$fileName") {
            "Path $PSScriptRoot\$fileName exists!"
        }
        else {
            $output = "$PSScriptRoot\$fileName"

            Start-BitsTransfer -Source $url -Destination $output
            Start-Sleep -s 5
        }
        if ($fileName -eq "7z2106-x64.msi") {
            Write-Host "retrieve 7zip and extract`r`n"
            $file = Get-ChildItem "$PSScriptRoot\7z2106-x64.msi"
            $DataStamp = get-date -Format yyyyMMddTHHmmss
            $logFile = '{0}-{1}.log' -f $file.fullname, $DataStamp
            $MSIArguments = @(
                "/a"
            ('"{0}"' -f $file.fullname)
                "/qn"
                "TARGETDIR=$PSScriptRoot\7z"
                "/norestart"
                "/L*v"
                $logFile
            )
            Write-host FILE = $file "msiexec.exe" -ArgumentList $MSIArguments -Wait -NoNewWindow 
            Start-Process "msiexec.exe" -ArgumentList $MSIArguments -Wait -NoNewWindow 
            Move-Item "$PSScriptRoot\7z\files\7-Zip" "$PSScriptRoot"
            Remove-Item -Recurse  "$PSScriptRoot\7z"
        }
        else {
            Write-Host "Extract $fileName to $OutPutFolder`r`n"
            Write-host Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\$fileName -o$OutPutFolder"
            Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\$fileName -o$OutPutFolder"
               
        }

        Write-Output "Time taken: $((Get-Date).Subtract($start_time).Seconds) second(s)"

    }
}



function ExtractCentaur {
    if (Test-Path -Path $PSScriptRoot\home) {
        Write-host "Nothing to do folder /home/pi/centaur is already there`r`n"
    }
    else {

        if (Test-Path -Path $PSScriptRoot\centaur.img) {
            Write-host "Nothing to do file centaur.img is already there`r`n"
        }
        else {
            Write-Host "We need to extract centaur from your sdcard`r`n"
            Write-Host "- please place original SDCard in your Card Reader"
            Write-Host "And use Win32DiskImager to create an Image file called centaur.img !"
            Start-Sleep -s $SleepTime
            Start-Process "$PSScriptRoot\Win32DiskImager\Win32DiskImager.exe"  -Wait -ArgumentList  "$PSScriptRoot\centaur.img"
        }
        Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\centaur.img 1.img"
        Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\centaur.img 1.img"

        Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\centaur.img 2.img"
        Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\centaur.img 2.img"
        Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\1.img home\pi\centaur"
        Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\1.img home\pi\centaur -xr!settings"
	Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\2.img  settings_1_2.dat running.info playscreendata_1_2.dat factory.info epaper_vcom.info clockdata_1_2.dat chesstime_1_2.dat chessgame_1_2.dat -o.\home\pi\centaur\settings"
        Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\2.img epaper* *.dat *.info -o.\home\pi\centaur\settings"
        Remove-Item  "$PSScriptRoot\1.img"
        Remove-Item  "$PSScriptRoot\2.img"
    }

}

function RaspiosImager {
    Write-host " "
    Write-host " Do you need to write a new SDCard with Raspbian"
    Write-host " using Raspberry PI imager?"
    Write-host " "
    Write-host " - DO NOT use your original Centaur card !!!"
    Write-host " "
    Start-Sleep -s $SleepTime
    
    $wshell = New-Object -ComObject Wscript.Shell
    $answer = $wshell.Popup("Do you need to write a new SDCard with Raspbian?", 0, "Alert", 64 + 4)
    if ($answer -eq 6) {

        Write-host " "
        Write-host " Please write the raspbian image to a new SDCard "
        Write-host " - DO NOT use your original Centaur card !!!"
        Write-host " "
        Write-host " - Use CNTRL + SHIFT + ""x"" in the ""Raspberry PI Imager"" tool!!!"
        Write-host " "
        Start-Sleep -s $SleepTime
        Start-Process "$PSScriptRoot\RaspberryPi_imager\rpi-imager.exe" -Wait
    }
    else {
        Write-host " "
        Write-host "  Centaur is extracted from your SDCard as centaur.tar.gz "
        Write-host "  The Program is finished"
        Write-host " "
        Start-Sleep -s 15
        exit 0
    }
}

function GetReleaseFile {
    if ($dev -eq 1) {
        $wshell = New-Object -ComObject Wscript.Shell
        $answer = $wshell.Popup("Do you want to use the release version $releaseFileName", 0, "Alert", 64 + 4)
    }
    else {
        $answer = 6
    }
    if ($answer -eq 7) {
        Add-Type -AssemblyName System.Windows.Forms
        $FileBrowser = New-Object System.Windows.Forms.OpenFileDialog -Property @{
            Multiselect = $false # Multiple files can be chosen
            Filter      = 'debian Package (*.deb)|*.deb' # Specified file types
        }
 
        [void]$FileBrowser.ShowDialog()

        $FilePath = $FileBrowser.FileName;
        #$FileName = (Get-ChildItem $FilePath).Name
        #$FilePath = (Get-ChildItem $FilePath).FullName

        If ($FileBrowser.FileNames -like "*\*") {

            # Do something 
            $FileBrowser.FileName #Lists selected files (optional)
	
        }
        else {
            Write-Host "Cancelled by user"
        }

    }
    else {
        if (Test-Path -Path $PSScriptRoot\$releaseFileName) {
            Write-host file $releaseFileName is ready downloaded
       
        }
        else {
            Start-BitsTransfer -Source $releaseUrl -Destination "$PSScriptRoot\$releaseFileName"

        }
        $FilePath = (Get-ChildItem "$PSScriptRoot\$releaseFileName").FullName
    }
    #WRITE-HOST "ReleaseName = $FileName"
    WRITE-HOST "ReleasePath = $FilePath"
    #Start-Sleep -s $SleepTime
    return $FilePath
}

function PickSDCardDriveName {
    do {
        Write-host " "
        Write-host " "
        write-host Select the Drive with the Raspbian Boot drive
        Write-host " "
        Write-host The drive should contain files config.txt and cmdline.txt
        Write-host " "
        Start-Sleep -s $SleepTime
        Add-Type -AssemblyName System.Windows.Forms
        $browser = New-Object System.Windows.Forms.FolderBrowserDialog
        $null = $browser.ShowDialog()
        $BootDrive = $browser.SelectedPath

        write-host $BootDrive

    } until ( Test-Path -Path $BootDrive\config.txt )
    return  $BootDrive
}

function ModifyBootDrive {
    Write-host "Write firstrun.sh to $BootDrive"
    Copy-Item "$BootDrive\firstrun.sh" -Destination ("$BootDrive\firstrun.sh" + "_" + $(get-date -f yyyy-MM-dd-HH-mm-ss) + "_bak")
    (Get-Content "$BootDrive\firstrun.sh") -notmatch "exit 0" | Set-Content "$BootDrive\firstrun_new.sh"
    $From = Get-Content -Path "$PSScriptRoot\add2firstrun.txt"
    Add-Content -Path  "$BootDrive\firstrun_new.sh" -Value $From
    #Get-Content -Path  "$BootDrive\firstrun_new.sh"
    (Get-Content "$BootDrive\firstrun_new.sh" -Raw).Replace("`r`n", "`n") | Set-Content "$BootDrive\firstrun.sh" -Force
    Remove-Item  "$BootDrive\firstrun_new.sh"

    Write-host "Write firstboot.py to $BootDrive"
    (Get-Content "$PSScriptRoot\firstboot.py") `
        -replace 'DGT.*?\.deb', $releaseFileName | `
        Out-File "$BootDrive\firstboot.py"
    (Get-Content "$BootDrive\firstboot.py" -Raw).Replace("`r`n", "`n") | Set-Content "$BootDrive\firstboot.py" -Force
     Copy-Item "$PSScriptRoot\lib" -Destination "$BootDrive\lib" -Recurse

    Write-host "Write firstboot.service to $BootDrive"
    Copy-Item "$PSScriptRoot\firstboot.service" -Destination "$BootDrive\firstboot.service"

    Write-host "Write original DGT Centaur software to $BootDrive"
    Copy-Item "$PSScriptRoot\home\pi\centaur" -Destination "$BootDrive\" -Recurse 
    
    Write-host "Write $releaseFileName to $BootDrive"
    Copy-Item "$releaseFilePath" -Destination "$BootDrive\$releaseFileName"



    # modify cmdline.txt and config.txt for CentaurMods to work AND gain accees to the Display during installation

    # Enabke SPI bus if not enbaled
    # $BootDrive = "H:\"

    $CONFIG = "$BootDrive\config.txt"
    $CMDLINEFILE = "$BootDrive\cmdline.txt"
    
    if ( ! (Select-String -Path $CONFIG -Pattern "#dgtcentaurmod"  -Quiet) ) {
        Add-Content -Path $CONFIG -Value ''
        Add-Content -Path $CONFIG -Value '#dgtcentaurmod'
        Add-Content -Path $CONFIG -Value ''
    }
    Write-host "Modify  $CONFIG and $CMDLINEFILE"
    Copy-Item "$CMDLINEFILE" -Destination ("$CMDLINEFILE" + "_" + $(get-date -f yyyy-MM-dd-HH-mm-ss) + "_bak")
    Copy-Item "$CONFIG" -Destination ("$CONFIG" + "_" + $(get-date -f yyyy-MM-dd-HH-mm-ss) + "_bak")

    Write-Host "::: Checking SPI"
    $SPIOFF = (Select-String -Path $CONFIG -Pattern "^#dtparam=spi=on"  -Quiet)
    Write-Host "SPIOFF $SPIOFF"

    if ($SPIOFF) {
    ((Get-Content -path $CONFIG -Raw) -replace '#dtparam=spi=on', 'dtparam=spi=on') | Set-Content -Path $CONFIG
    }
    else {
        if (Select-String -Path $CONFIG -Pattern "^dtparam=spi=on"  -Quiet) {
            Write-Host "$CONFIG is already changed to SPION"
        }
        else {
            Add-Content -Path $CONFIG -Value 'dtparam=spi=on'
        }
    } 

    Write-Host ":::::: Checking SPI 1.0 bus."
    $SPI10 = (Select-String -Path $CONFIG -Pattern "^dtoverlay=spi1-3cs"  -Quiet)
    Write-Host "SPI10 $SPI10"
    if ( ! $SPI10 ) {
        Write-Host "We add dtoverlay=spi1-3cs"
        Add-Content -Path $CONFIG -Value 'dtoverlay=spi1-3cs'
    }
    else {
        Write-Host "$CONFIG is already changed for dtoverlay=spi1-3cs"
    }
  
    
    Write-Host "::: Checking serial port. "
    $UARTOFF = (Select-String -Path $CONFIG -Pattern "^#enable_uart=1"  -Quiet)
    Write-Host "UARTOFF $UARTOFF"
    if ($UARTOFF) {
        Write-Host "::: Enabling serial port..."
    ((Get-Content -path $CONFIG -Raw) -replace '#enable_uart=1', 'enable_uart=1') | Set-Content -Path $CONFIG
    }
    else {
        if (Select-String -Path $CONFIG -Pattern "^enable_uart=1"  -Quiet) {
            Write-Host "$CONFIG is already changed to UARTON"
        }
        else {
            Add-Content -Path $CONFIG -Value 'enable_uart=1'
        }
    }
    (Get-Content "$CONFIG" -Raw).Replace("`r`n", "`n") | Set-Content "$CONFIG" -Force
    Write-host "::: Disable console on ttyS0"
((Get-Content -path $CMDLINEFILE -Raw) -replace 'console=serial0,115200 ', '') | Set-Content -Path $CMDLINEFILE
(Get-Content "$CMDLINEFILE" -Raw).Replace("`r`n", "`n") | Set-Content "$CMDLINEFILE" -Force
    Write-host " "
    Write-host "  The SDCard is ready for the Centaur"
    Write-host "  Plug into your Pi Zero w 2 and power on"
    Write-host " "
    Write-host "  Be careful with the epaper display - it is very fragile!"
    Write-host " "
    Write-host "  Be patient on the first boot - it takes time while it upgrades "
    Write-host "  all the software already installed on the raspios!"
    Start-Sleep -s 15
}

retrieveFiles -URL "https://7-zip.org/a/7z2106-x64.msi" -fileName "7z2106-x64.msi" -OutPutFolder "7-Zip"
retrieveFiles -URL "https://sourceforge.net/projects/win32diskimager/files/Archive/Win32DiskImager-1.0.0-binary.zip/download" -fileName "Win32DiskImager-1.0.0-binary.zip" -OutPutFolder "Win32DiskImager"
retrieveFiles -URL "https://downloads.raspberrypi.org/imager/imager_latest.exe" -fileName "raspberryPi_imager_latest.exe" -OutPutFolder "RaspberryPi_imager"

ExtractCentaur
RaspiosImager
$FilePathAll = GetReleaseFile 
If ( $FilePathAll[0].length -eq 1) {
    $releaseFilePath = $FilePathAll
}
else {
    $releaseFilePath = $FilePathAll[0]
}
write-host "releaseFilePath $releaseFilePath"
$releaseFileName = (Get-ChildItem $releaseFilePath).Name
Write-Host "releaseFileName $releaseFileName"
$BootDrive = PickSDCardDriveName 
Write-Host "DriveName $BootDrive"
ModifyBootDrive

exit 0
