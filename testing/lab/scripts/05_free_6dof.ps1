# 05 — SLOBODNO GIBANJE, CIJELA RUKA (6-DOF mimikrija zglob-na-zglob)
#
# Rame yaw/pitch -> J1/J2, lakat -> J3, zglob flex/dev/axial -> J4/J5/J6.
# NIJE inverzna kinematika nego mimikrija: svaki kanal vozi svoj zglob.
#
# PRIJE OVOGA: 04_kalibracija_osi.ps1. Ako arm_axes ne odgovara trenutnim krutim
# tijelima, zglobovi će reagirati na krive pokrete ili u krivom smjeru — zato ovdje
# granice starta konzervativno (+-25 deg, 20 deg/s), pa ih dižeš kad potvrdiš smjerove.
#
#   .\05_slobodno_6dof.ps1
#   .\05_slobodno_6dof.ps1 -RangeDps 45 -SpeedDps 40 -Seconds 90

param(
    [string]$RobotIp  = "192.168.40.50",
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30",
    [double]$Seconds  = 60,
    [double]$RangeDps = 25,
    [double]$SpeedDps = 20,
    [int]$Port        = 51000,
    [string]$Tag      = "arm6dof",
    [switch]$NoHome
)

. "$PSScriptRoot\_common.ps1"

$outDir = Join-Path $script:RepoRoot "testing/lab\results\free"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base  = Join-Path $outDir "$Tag`_$stamp"

Write-Head "05 — SLOBODNO GIBANJE 6-DOF" @{
    Robot = $RobotIp; Trajanje = "$Seconds s"
    Granice = "+-$RangeDps deg, $SpeedDps deg/s (po zglobu)"; Zapis = (Split-Path $base -Leaf)
}

Write-Host "`nSVIH ŠEST ZGLOBOVA PRATI RUKU. Ako smjer izgleda krivo — Ctrl-C i 04_kalibracija_osi.ps1." -ForegroundColor Yellow
Write-Host "Nitko u radnom prostoru robota. E-stop u ruci." -ForegroundColor Yellow
Read-Host "Enter za nastavak (Ctrl-C za odustajanje)" | Out-Null

if (-not $NoHome) {
    Write-Host "`n-> referentna poza ..."
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--yes")
}

$bridge = $null
try {
    $bridge = Start-Bridge -Mode arm -ServerIp $MotiveIp -ClientIp $ClientIp -Port $Port
    Write-Host "`n-> pipeline (multi_joint): $Seconds s. Kreni iz ISPRUŽENE ruke.`n"
    Invoke-Py @("-m", "src.pipeline.main",
        "--external", "--port", "$Port",
        "--mode", "multi_joint",
        "--sink", "ur3e", "--ip", $RobotIp,
        "--seconds", "$Seconds",
        "--range-dps", "$RangeDps", "--max-speed-dps", "$SpeedDps",
        "--latency-csv", "$base.csv",
        "--track-csv", "$base.track.csv", "--log-actual")
}
finally {
    Stop-Bridge $bridge
}

if (Test-Path "$base.track.csv") {
    Write-Host "`n-> analiza po zglobovima:`n"
    Invoke-Py @("-m", "src.tools.track_analysis", "$base.track.csv")
}
Write-Host "`nZapisi: $base.*"
