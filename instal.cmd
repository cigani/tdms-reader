@echo off
echo Param(>run.ps1
echo     [Parameter(Mandatory=$true, Position=0, HelpMessage="Please Entire your data directory")]>>run.ps1
echo     [string]$filepath>>run.ps1
echo   )>>run.ps1
echo # ~~~~~~~~~~~~~~~~~~ Paths ~~~~~~~~~~~~~~~~~~ #>>run.ps1
echo $username = $env:USERNAME>>run.ps1
echo $pythonVersion = "3.8.5">>run.ps1
echo $pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion.exe">>run.ps1
echo $pythonDownloadPath = "C:\Users\$username\python-$pythonVersion.exe">>run.ps1
echo $pythonInstallDir = "C:\Users\$username\Python$pythonVersion">>run.ps1
echo $pythonScriptDir = "$pythonInstallDir\Scripts">>run.ps1
echo $application = "tdms-reader">>run.ps1
echo $venvDir = "$pythonInstallDir\venv\$application">>run.ps1
echo # ~~~~~~~~~~~~~~~~~~ Python ~~~~~~~~~~~~~~~~~~ #>>run.ps1
echo if (-Not (Test-Path $pythonInstallDir)) {>>run.ps1
echo     (New-Object Net.WebClient).DownloadFile($pythonUrl, $pythonDownloadPath)>>run.ps1
echo     ^& $pythonDownloadPath /quiet InstallAllUsers=0 Include_launcher=0 Include_test=0 SimpleInstall=1 SimpleInstallDescription="Just for me, no test suite."  TargetDir=$pythonInstallDir>>run.ps1
echo     if ($LASTEXITCODE -ne 0) {>>run.ps1
echo         throw "The python installer at '$pythonDownloadPath' exited with error code '$LASTEXITCODE'">>run.ps1
echo     }>>run.ps1
echo Remove-Item $pythonDownloadPath>>run.ps1
echo }>>run.ps1
echo $env:path = "$pythonInstallDir;${pythonScriptDir}">>run.ps1
echo pip install virtualenv -q>>run.ps1
echo if (-Not (Test-Path $venvDir)){>>run.ps1
echo virtualenv $venvDir>>run.ps1
echo }>>run.ps1
echo Set-Location $venvDir/Scripts>>run.ps1
echo ./activate>>run.ps1
echo # ~~~~~~~~~~~~~~~~~~ Package ~~~~~~~~~~~~~~~~~~ #>>run.ps1
echo pip install $application -q>>run.ps1
echo pip install $application -Uq>>run.ps1
echo $app = $application.Replace('-', '_')>>run.ps1
echo python -m $app --data=$filepath>>run.ps1

SET ThisScriptsDirectory=%~dp0
SET PowerShellScriptPath=%ThisScriptsDirectory%\run.ps1
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '%PowerShellScriptPath%'"
