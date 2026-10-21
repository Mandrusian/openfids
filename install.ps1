# OpenFIDS one-line installer for Windows (PowerShell).
#   irm https://raw.githubusercontent.com/Mandrusian/openfids/main/install.ps1 | iex
# Options: $env:OPENFIDS_DIR (default ~\openfids), $env:OPENFIDS_REF (default main)
$ErrorActionPreference = 'Stop'
$Repo = 'Mandrusian/openfids'
$Ref  = if ($env:OPENFIDS_REF) { $env:OPENFIDS_REF } else { 'main' }
$Dest = if ($env:OPENFIDS_DIR) { $env:OPENFIDS_DIR } else { Join-Path $HOME 'openfids' }

if ((Test-Path $Dest) -and (Get-ChildItem $Dest -Force | Select-Object -First 1) -and -not (Test-Path (Join-Path $Dest 'app\server.py'))) {
    throw "$Dest already exists and doesn't look like OpenFIDS. Set `$env:OPENFIDS_DIR to another folder."
}

$tmp = Join-Path ([IO.Path]::GetTempPath()) ('openfids-' + [guid]::NewGuid())
New-Item -ItemType Directory $tmp | Out-Null
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Write-Host "Downloading OpenFIDS ($Ref) ..."
    $zip = Join-Path $tmp 'src.zip'
    Invoke-WebRequest "https://codeload.github.com/$Repo/zip/$Ref" -OutFile $zip -UseBasicParsing
    Expand-Archive $zip -DestinationPath $tmp
    $src = Get-ChildItem $tmp -Directory | Select-Object -First 1
    New-Item -ItemType Directory $Dest -Force | Out-Null
    Copy-Item (Join-Path $src.FullName '*') $Dest -Recurse -Force
} finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
Set-Location $Dest
& cmd.exe /c install_windows.bat
