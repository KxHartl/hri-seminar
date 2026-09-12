# 02 — SLOBODNO GIBANJE: praćenje svih 6 zglobova (6-DOF) ili pojedinog zgloba (1-DOF)
#
# ZADANO: SVIH 6 ZGLOBOVA (6-DOF mimikrija cijele ruke: rame yaw/pitch -> J1/J2,
# lakat -> J3, zapešće flex/dev/axial -> J4/J5/J6).
# Ako želiš voziti samo jedan zglob (1-DOF kut lakta -> Jx), proslijedi npr. -Joint 2 (J3).
#
#   .\02_slobodno_gibanje.ps1                       # SVIH 6 zglobova (6-DOF), kontinuirano do Ctrl-C
#   .\02_slobodno_gibanje.ps1 -Seconds 60           # 6-DOF s limitom 60 s
#   .\02_slobodno_gibanje.ps1 -RangeDps 60          # 6-DOF, šire granice
#   .\02_slobodno_gibanje.ps1 -Joint 2              # 1-DOF samo lakat -> J3 (T-02)

param(
    [string]$RobotIp  = "192.168.40.50",
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30",
    [int]$Joint       = -1,           # -1 = SVIH 6 ZGLOBOVA (6-DOF); 0..5 = samo odabrani zglob (1-DOF)
    [double]$Seconds  = 0,            # 0 = KONTINUIRANO (bez time limita, prekid s Ctrl-C)
    [double]$RangeDps = 90,           # dopušteni +- otklon [deg] (široke granice za slobodno gibanje)
    [double]$SpeedDps = 150,          # gornja granica brzine zgloba [deg/s]
    [int]$Port        = 51000,
    [string]$Tag      = "slobodno",
    [switch]$NoHome                   # preskoči povratak u referentnu pozu
)

. "$PSScriptRoot\_common.ps1"

$is6Dof = ($Joint -lt 0)

$outDir = Join-Path $script:RepoRoot "testing/lab\results\free"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

if ($is6Dof) {
    $base       = Join-Path $outDir "$Tag`_6dof_$stamp"
    $titleDesc  = "02 — SLOBODNO GIBANJE (6-DOF, svih 6 zglobova)"
    $bridgeMode = "arm"
    $pyArgs = @("-m", "src.pipeline.main",
        "--external", "--port", "$Port",
        "--mode", "multi_joint",
        "--sink", "ur3e", "--ip", $RobotIp,
        "--seconds", "$Seconds",
        "--range-dps", "$RangeDps", "--max-speed-dps", "$SpeedDps",
        "--latency-csv", "$base.csv",
        "--track-csv", "$base.track.csv", "--log-actual")
} else {
    $base       = Join-Path $outDir "$Tag`_J$($Joint + 1)_$stamp"
    $titleDesc  = "02 — SLOBODNO GIBANJE (1-DOF: lakat -> zglob $($Joint + 1))"
    $bridgeMode = "sdk"
    $pyArgs = @("-m", "src.pipeline.main",
        "--external", "--port", "$Port",
        "--sink", "ur3e", "--ip", $RobotIp,
        "--joint", "$Joint", "--seconds", "$Seconds",
        "--range-dps", "$RangeDps", "--max-speed-dps", "$SpeedDps",
        "--latency-csv", "$base.csv",
        "--track-csv", "$base.track.csv", "--log-actual")
}

$durText = if ($Seconds -gt 0) { "$Seconds s" } else { "kontinuirano (prekid: Ctrl-C)" }

Write-Head $titleDesc @{
    Robot = $RobotIp; Motive = $MotiveIp; Trajanje = $durText
    Granice = "+-$RangeDps deg, $SpeedDps deg/s"; Zapis = (Split-Path $base -Leaf)
}

if ($is6Dof) {
    Write-Host "`nSVIH ŠEST ZGLOBOVA PRATI GIBANJE RUKE (6-DOF mimikrija)." -ForegroundColor Yellow
    Write-Host "Kreni s ISPRUŽENOM rukom (referentna poza)." -ForegroundColor Yellow
} else {
    Write-Host "`nZGLOB $($Joint + 1) PRATI GIBANJE LAKTA (1-DOF)." -ForegroundColor Yellow
}
Write-Host "Nitko u radnom prostoru robota. E-stop u ruci. Prekid i spremanje: Ctrl-C." -ForegroundColor Yellow
Read-Host "Enter za nastavak (Ctrl-C za odustajanje)" | Out-Null

if (-not $NoHome) {
    Write-Host "`n-> referentna poza ..."
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--yes")
}

$bridge = $null
try {
    $bridge = Start-Bridge -Mode $bridgeMode -ServerIp $MotiveIp -ClientIp $ClientIp -Port $Port
    Write-Host "`n-> pipeline: $durText. Kreni s pokretom. Zaustavi s Ctrl-C.`n"
    Invoke-Py $pyArgs
}
finally {
    Stop-Bridge $bridge
}

if (Test-Path "$base.track.csv") {
    Write-Host "`n-> analiza vjernosti praćenja:`n"
    Invoke-Py @("-m", "src.tools.track_analysis", "$base.track.csv")
}
Write-Host "`nZapisi: $base.*"
