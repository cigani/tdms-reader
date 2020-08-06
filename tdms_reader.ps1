Param(
    [Parameter(Mandatory=$true, Position=0, HelpMessage="Please Entire your data directory")]
    [string]$filepath
  )
# ~~~~~~~~~~~~~~~~~~ Paths ~~~~~~~~~~~~~~~~~~ #
$username = $env:USERNAME
$pythonVersion = "3.8.5"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion.exe"
$pythonDownloadPath = "C:\Users\$username\python-$pythonVersion.exe"
$pythonInstallDir = "C:\Users\$username\Python$pythonVersion"
$pythonScriptDir = "$pythonInstallDir\Scripts"
$application = "tdms-reader"
$venvDir = "$pythonInstallDir\venv\$application"

# ~~~~~~~~~~~~~~~~~~ Python ~~~~~~~~~~~~~~~~~~ #
if (-Not (Test-Path $pythonInstallDir)) {
    (New-Object Net.WebClient).DownloadFile($pythonUrl, $pythonDownloadPath)
    & $pythonDownloadPath /quiet InstallAllUsers=0 Include_launcher=0 Include_test=0 SimpleInstall=1 SimpleInstallDescription="Just for me, no test suite."  TargetDir=$pythonInstallDir
    if ($LASTEXITCODE -ne 0) {
        throw "The python installer at '$pythonDownloadPath' exited with error code '$LASTEXITCODE'"
    }
Remove-Item $pythonDownloadPath
}

$env:path = "$pythonInstallDir;${pythonScriptDir}"
pip install virtualenv -q
if (-Not (Test-Path $venvDir)){
virtualenv $venvDir
}
Set-Location $venvDir/Scripts
./activate
Set-Location $filepath

# ~~~~~~~~~~~~~~~~~~ Package ~~~~~~~~~~~~~~~~~~ #
pip install $application -q
pip install $application -Uq
$app = $application.Replace('-', '_')
python -m $app --data=$filepath
