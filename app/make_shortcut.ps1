param([Parameter(Mandatory = $true)][string]$Root)
$ErrorActionPreference = 'Stop'
$root   = (Resolve-Path $Root).Path
$python = Join-Path $root '.venv\Scripts\pythonw.exe'   # pythonw = no console window
$script = Join-Path $root 'app\launcher.py'
$icon   = Join-Path $root 'app\icon.ico'
$shell  = New-Object -ComObject WScript.Shell
$targets = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
foreach ($dir in $targets) {
    if (-not $dir -or -not (Test-Path $dir)) { continue }
    $lnk = $shell.CreateShortcut((Join-Path $dir 'OpenFIDS.lnk'))
    $lnk.TargetPath       = $python
    $lnk.Arguments        = '"' + $script + '"'
    $lnk.WorkingDirectory = $root
    $lnk.IconLocation     = $icon
    $lnk.Description      = 'Cairns Airport FIDS (runs locally)'
    $lnk.Save()
}
