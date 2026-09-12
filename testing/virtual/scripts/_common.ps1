# Shared helpers for testing/virtual scripts. Dot-source this, do not run directly:
#   . "$PSScriptRoot\_common.ps1"

$ErrorActionPreference = "Stop"

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$script:Py = Join-Path $script:RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $script:Py)) {
    throw "Ne nalazim .venv python: $script:Py (potreban za ur_rtde)"
}

function Write-Head([string]$Title, [hashtable]$Info) {
    Write-Host ("=" * 78)
    Write-Host $Title
    foreach ($k in $Info.Keys) { Write-Host ("  {0,-16} {1}" -f $k, $Info[$k]) }
    Write-Host ("=" * 78)
}

function Test-PortFree([int]$Port) {
    $used = Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue
    if ($used) {
        throw "UDP port $Port je zauzet (PID $($used.OwningProcess)). Ugasi stari proces pa ponovi."
    }
}

function Start-MockBridge([int]$Port = 51000) {
    Test-PortFree $Port
    $a = @("-m", "src.tools.live_sender", "--mock-arm", "--port", "$Port")
    Write-Host "-> Pokrecem mock 6-DOF bridge (live_sender --mock-arm) na 127.0.0.1:$Port ..."
    $p = Start-Process -FilePath $script:Py -ArgumentList $a -WorkingDirectory $script:RepoRoot `
                       -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 2
    if ($p.HasExited) {
        throw "Mock bridge je pao s kodom $($p.ExitCode)."
    }
    Write-Host "   Mock bridge aktivan (PID $($p.Id))."
    return $p
}

function Start-LiveBridge {
    param(
        [string]$ServerIp = "192.168.40.31",
        [string]$ClientIp = "192.168.40.30",
        [int]$Port = 51000
    )
    Test-PortFree $Port
    $a = @("-m", "src.tools.live_sender", "--arm",
           "--server-ip", $ServerIp, "--client-ip", $ClientIp, "--port", "$Port")
    Write-Host "-> Pokrecem zivi 6-DOF bridge prema Motiveu $ServerIp -> 127.0.0.1:$Port ..."
    $p = Start-Process -FilePath $script:Py -ArgumentList $a -WorkingDirectory $script:RepoRoot `
                       -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 3
    if ($p.HasExited) {
        throw "Bridge je pao s kodom $($p.ExitCode). Provjeri Motive streaming i mrezu."
    }
    Write-Host "   Zivi bridge aktivan (PID $($p.Id))."
    return $p
}

function Stop-Bridge($Proc) {
    if ($null -ne $Proc -and -not $Proc.HasExited) {
        Write-Host "-> Zaustavljam bridge (PID $($Proc.Id)) ..."
        Stop-Process -Id $Proc.Id -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-Py {
    param([string[]]$PyArgs)
    Push-Location $script:RepoRoot
    try {
        & $script:Py @PyArgs
        $script:LastPyExit = $LASTEXITCODE
    }
    finally { Pop-Location }
}
