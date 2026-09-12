# Shared helpers for the lab run scripts. Dot-source this, do not run it directly.
#
#   . "$PSScriptRoot\_common.ps1"
#
# Owns the two things every run needs and everyone gets wrong under time pressure:
# resolving the repo's venv python, and starting/stopping exactly ONE bridge
# process on the UDP port (two bridges look like 240 Hz and 38 % packet loss).

$ErrorActionPreference = "Stop"

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$script:Py = Join-Path $script:RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $script:Py)) {
    throw "Ne nalazim .venv python: $script:Py  (sustavski python nema ur_rtde)"
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
        throw "UDP port $Port je zauzet (PID $($used.OwningProcess)). Ugasi stari most pa ponovi."
    }
}

# Starts live_sender in its own minimized window and returns the process object.
# Mode: 'sdk' = 1-DOF elbow angle, 'arm' = full 6-DOF arm channels.
function Start-Bridge {
    param(
        [ValidateSet("sdk", "arm")][string]$Mode = "sdk",
        [string]$ServerIp = "192.168.40.31",
        [string]$ClientIp = "192.168.40.30",
        [int]$Port = 51000,
        [int]$IdUpper = 25, [int]$IdFore = 24, [int]$IdHand = 16
    )
    Test-PortFree $Port
    $a = @("-m", "src.tools.live_sender", "--$Mode",
           "--server-ip", $ServerIp, "--client-ip", $ClientIp, "--port", "$Port",
           "--id-upper", "$IdUpper", "--id-fore", "$IdFore", "--id-hand", "$IdHand")
    Write-Host "-> most (live_sender --$Mode) $ServerIp -> 127.0.0.1:$Port ..."
    $p = Start-Process -FilePath $script:Py -ArgumentList $a -WorkingDirectory $script:RepoRoot `
                       -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 3
    if ($p.HasExited) {
        throw "Most je odmah pao (izlazni kod $($p.ExitCode)). Provjeri Motive: streaming ON, unicast, ID-evi."
    }
    Write-Host "   most radi (PID $($p.Id))."
    return $p
}

function Stop-Bridge($Proc) {
    if ($null -ne $Proc -and -not $Proc.HasExited) {
        Write-Host "-> gasim most (PID $($Proc.Id)) ..."
        Stop-Process -Id $Proc.Id -Force -ErrorAction SilentlyContinue
    }
}

# Runs the repo's venv python FROM THE REPO ROOT (so `-m src.tools.x` resolves) and
# leaves its output on the console. The exit code lands in $script:LastPyExit rather
# than on the pipeline, so callers never have to swallow output with Out-Null.
#
# NOTE: the parameter must NOT be called $Args — that is PowerShell's automatic
# variable inside a function, so splatting it would pass nothing and python would
# drop into an interactive REPL.
function Invoke-Py {
    param([string[]]$PyArgs)
    Push-Location $script:RepoRoot
    try {
        & $script:Py @PyArgs
        $script:LastPyExit = $LASTEXITCODE
    }
    finally { Pop-Location }
}
