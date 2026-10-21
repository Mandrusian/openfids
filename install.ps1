$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Repo = 'Mandrusian/openfids'
$Ref = if ($env:OPENFIDS_REF) { $env:OPENFIDS_REF } else { 'main' }
$Dest = if ($env:OPENFIDS_DIR) { $env:OPENFIDS_DIR } else { Join-Path $HOME 'openfids' }

if ((Test-Path $Dest) -and (Get-ChildItem $Dest -Force | Select-Object -First 1) -and -not (Test-Path (Join-Path $Dest 'app\server.py'))) {
    throw "$Dest already exists and doesn't look like OpenFIDS. Set OPENFIDS_DIR to another folder."
}

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ('openfids-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $Tmp | Out-Null

try {
    Write-Host "Downloading OpenFIDS ($Ref)..."
    $Zip = Join-Path $Tmp 'source.zip'
    Invoke-WebRequest "https://codeload.github.com/$Repo/zip/refs/heads/$Ref" -OutFile $Zip
    Expand-Archive -LiteralPath $Zip -DestinationPath $Tmp

    $Src = Get-ChildItem $Tmp -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'app\server.py') } | Select-Object -First 1
    if (-not $Src) { throw 'Downloaded archive does not contain app\server.py.' }

    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    Copy-Item (Join-Path $Src.FullName '*') $Dest -Recurse -Force
}
finally {
    Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue
}

$Dest = [IO.Path]::GetFullPath($Dest)
Set-Location $Dest

foreach ($Required in @('app\server.py','app\requirements.txt','app\launcher.py')) {
    if (-not (Test-Path (Join-Path $Dest $Required) -PathType Leaf)) {
        throw "Required OpenFIDS file is missing: $Required"
    }
}

function Find-Python {
    foreach ($Name in @('py', 'python')) {
        $Command = Get-Command $Name -ErrorAction SilentlyContinue
        if (-not $Command) { continue }

        $Prefix = if ($Name -eq 'py') { @('-3') } else { @() }
        & $Command.Source @Prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' *> $null
        if ($LASTEXITCODE -eq 0) {
            $Exe = & $Command.Source @Prefix -c 'import sys; print(sys.executable)' *> $null
            if ($LASTEXITCODE -eq 0 -and $Exe) { return [string]$Exe[-1] }
        }
    }

    foreach ($Version in @('313','312','311','310','39')) {
        foreach ($Base in @("$env:LOCALAPPDATA\Programs\Python", $env:ProgramFiles)) {
            $Candidate = Join-Path $Base "Python$Version\python.exe"
            if (Test-Path $Candidate) {
                & $Candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' *> $null
                if ($LASTEXITCODE -eq 0) { return $Candidate }
            }
        }
    }

    return $null
}

$PY = Find-Python

if (-not $PY) {
    Write-Host 'Python 3.9+ not found. Installing Python 3.12...'
    $Winget = Get-Command winget -ErrorAction SilentlyContinue

    if ($Winget) {
        & $Winget.Source install -e --id Python.Python.3.12 --scope user --silent --accept-source-agreements --accept-package-agreements
        $PY = Find-Python
    }

    if (-not $PY) {
        $Arch = if ([Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq 'Arm64') { 'arm64' } else { 'amd64' }
        $PyInstaller = Join-Path $env:TEMP 'openfids-python-setup.exe'

        try {
            Invoke-WebRequest "https://www.python.org/ftp/python/3.12.8/python-3.12.8-$Arch.exe" -OutFile $PyInstaller
            $Install = Start-Process -FilePath $PyInstaller -ArgumentList @('/quiet','InstallAllUsers=0','PrependPath=1','Include_test=0','Include_launcher=1') -Wait -PassThru
            if ($Install.ExitCode -ne 0) { throw "Python installer failed: exit code $($Install.ExitCode)" }
        }
        finally {
            Remove-Item $PyInstaller -Force -ErrorAction SilentlyContinue
        }

        $PY = Find-Python
    }
}

if (-not $PY) { throw 'Python installation failed. Install Python 3.12+ and rerun this installer.' }

Write-Host "Using Python: $PY"
Write-Host '[1/3] Creating private environment...'

$VenvPython = Join-Path $Dest '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
    & $PY -m venv (Join-Path $Dest '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}

Write-Host '[2/3] Installing requirements...'
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }

& $VenvPython -m pip install -r (Join-Path $Dest 'app\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

Write-Host '[3/3] Creating shortcuts...'
$ShortcutScript = Join-Path $Dest 'shortcut_windows.bat'
if (Test-Path $ShortcutScript) {
    & $env:ComSpec /d /c "`"$ShortcutScript`" nopause"
    if ($LASTEXITCODE -ne 0) { throw 'Shortcut creation failed.' }
}
else {
    Write-Warning 'shortcut_windows.bat is missing; skipping shortcuts.'
}

$Launcher = Join-Path $Dest 'app\launcher.py'
$PythonW = Join-Path $Dest '.venv\Scripts\pythonw.exe'

Write-Host 'Starting OpenFIDS...'
if (Test-Path $PythonW) {
    Start-Process -FilePath $PythonW -ArgumentList "`"$Launcher`"" -WorkingDirectory $Dest
}
else {
    Start-Process -FilePath $VenvPython -ArgumentList "`"$Launcher`"" -WorkingDirectory $Dest
}

Write-Host 'OpenFIDS launch requested. Check your browser.'
