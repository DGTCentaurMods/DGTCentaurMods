Import-Module BitsTransfer

$releaseVersion = '0.1.0'
$dev = '1'
$SleepTime = 1

$releaseFileName = -join ("DGTCentaurMods_" , $releaseVersion , "_armhf.deb" )
$releaseURL = -join ("https://github.com/EdNekebno/DGTCentaur/releases/download/", $releaseVersion , "/" , $releaseFileName )

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
        } else {
            $output = "$PSScriptRoot\$fileName"

            Start-BitsTransfer -Source $url -Destination $output
            Start-Sleep -s 5
        }
        if ($fileName -eq "7z2106-x64.msi") {
            "retrieve 7zip and extract"
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

            Write-host Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\$fileName -o$OutPutFolder"
            Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\$fileName -o$OutPutFolder"
               
        }

        Write-Output "Time taken: $((Get-Date).Subtract($start_time).Seconds) second(s)"

    }
}


retrieveFiles -URL "https://7-zip.org/a/7z2106-x64.msi" -fileName "7z2106-x64.msi" -OutPutFolder "7-Zip"
retrieveFiles -URL "https://sourceforge.net/projects/win32diskimager/files/Archive/Win32DiskImager-1.0.0-binary.zip/download" -fileName "Win32DiskImager-1.0.0-binary.zip" -OutPutFolder "Win32DiskImager"
retrieveFiles -URL "https://downloads.raspberrypi.org/imager/imager_latest.exe" -fileName "raspberryPi_imager_latest.exe" -OutPutFolder "RaspberryPi_imager"

if (Test-Path -Path $PSScriptRoot\centaur.tar.gz) {
    Write-host "Nothing to do file centaur.tar.gz is already there"
}
else {

    if (Test-Path -Path $PSScriptRoot\centaur.img) {
        Write-host "Nothing to do file centaur.img is already there"
    }
    else {
        Write-Host "We need to extract centaur from your sdcard"
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
    Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\1.img home\pi\centaur"
    Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\2.img  settings_1_2.dat running.info playscreendata_1_2.dat factory.info epaper_vcom.info clockdata_1_2.dat chesstime_1_2.dat chessgame_1_2.dat -o.\home\pi\centaur\settings"
    Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList "x $PSScriptRoot\2.img  settings_1_2.dat running.info playscreendata_1_2.dat factory.info epaper_vcom.info clockdata_1_2.dat chesstime_1_2.dat chessgame_1_2.dat -o.\home\pi\centaur\settings"
    Remove-Item  "$PSScriptRoot\1.img"
    Remove-Item  "$PSScriptRoot\2.img"
    Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList  "a $PSScriptRoot\centaur.tar  -ttar .\home\pi\centaur"
    Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList  "a $PSScriptRoot\centaur.tar  -ttar .\home\pi\centaur"
    Write-Host  Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList  "a $PSScriptRoot\centaur.tar.gz  -tgzip .\centaur.tar"
    Start-Process "$PSScriptRoot\7-Zip\7z.exe"  -Wait -ArgumentList  "a $PSScriptRoot\centaur.tar.gz  -tgzip .\centaur.tar"
    Remove-Item  "$PSScriptRoot\centaur.tar"
}
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
    Write-host " - Use CNTRL + SHIFT + ""x"" in the ""Raspberry Pi Imager"" to allow ssh AND configure your WIFI !!!"
    Write-host " "
    Start-Sleep -s $SleepTime
    Start-Process "$PSScriptRoot\RaspberryPi_imager\rpi-imager.exe" -Wait
} else {
    Write-host " "
    Write-host "  Centaur is extracted from your SDCard as centaur.tar.gz "
    Write-host "  The Program is finished"
    Write-host " "
    Start-Sleep -s 15
    exit 0
}
if ($dev -eq 1) {
    $wshell = New-Object -ComObject Wscript.Shell
    $answer = $wshell.Popup("Do you want to use the release version $releaseFileName", 0, "Alert", 64 + 4)
} else {
    $answer = 6
}
if ($answer -eq 7) {
    Add-Type -AssemblyName System.Windows.Forms
    $FileBrowser = New-Object System.Windows.Forms.OpenFileDialog -Property @{
        Multiselect = $false # Multiple files can be chosen
        Filter      = 'debian Package (*.deb)|*.deb' # Specified file types
    }
 
    [void]$FileBrowser.ShowDialog()

    $releaseFilePath = $FileBrowser.FileName;
    $releaseFileName = (Get-ChildItem $releaseFilePath).Name

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
    $releaseFilePath = "$PSScriptRoot\$releaseFileName"
}
WRITE-HOST ReleaseName =  $releaseFileName
WRITE-HOST ReleasePath = $releaseFilePath
Start-Sleep -s $SleepTime
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

(Get-Content "$BootDrive\firstrun.sh") -notmatch "exit 0" | Set-Content "$BootDrive\firstrun_new.sh"
$From = Get-Content -Path "$PSScriptRoot\add2firstrun.txt"
Add-Content -Path  "$BootDrive\firstrun_new.sh" -Value $From
#Get-Content -Path  "$BootDrive\firstrun_new.sh"
Write-host "Write firstboot.sh to $BootDrive"
(Get-Content "$PSScriptRoot\firstboot.sh") `
    -replace 'DGT.*?\.deb', $releaseFileName | `
    Out-File "$BootDrive\firstboot.sh"
Write-host "Write firstboot.service to $BootDrive"
Copy-Item "$PSScriptRoot\firstboot.service" -Destination "$BootDrive\firstboot.service"
Write-host "Write centaur.tar.gz to $BootDrive"
Copy-Item "$PSScriptRoot\centaur.tar.gz" -Destination "$BootDrive\centaur.tar.gz"
Write-host "Write $releaseFileName to $BootDrive"
Copy-Item "$releaseFilePath" -Destination "$BootDrive\$releaseFileName"
(Get-Content "$BootDrive\firstboot.sh" -Raw).Replace("`r`n", "`n") | Set-Content "$BootDrive\firstboot.sh" -Force
Write-host "Write firstrun.sh to $BootDrive"
(Get-Content "$BootDrive\firstrun_new.sh" -Raw).Replace("`r`n", "`n") | Set-Content "$BootDrive\firstrun.sh" -Force
Remove-Item  "$BootDrive\firstrun_new.sh"

