# 00_ursim_quicktest.ps1 — Brza provjera URSim-a u VMware-u
#
# Provjerava:
# 1. RTDE receive vezu (stanje simulatora)
# 2. RTDE servoJ sweep (+-5 deg)
# 3. 15 s testnog rada s replay podacima i logiranjem kutova

param(
    [string]$UrsimIp = "192.168.208.128",
    [switch]$NoMove
)

. "$PSScriptRoot\_common.ps1"

$rezimText = if ($NoMove) { "Samo stanje" } else { "Puni sweep + Replay test" }
Write-Head "PROVJERA URSIM SIMULATORA (VMware)" @{ "URSim" = $UrsimIp; "Rezim" = $rezimText }

Write-Host "`n[1/3] Provjera RTDE receive veze..."
Invoke-Py @("-m", "src.tools.check_ursim", "--ip", $UrsimIp, "--no-move")

if ($script:LastPyExit -ne 0) {
    Write-Host "`nGreška pri spajanju na URSim! Provjeri IP, Remote Control mod i da je robot uključen." -ForegroundColor Red
    exit 1
}

if ($NoMove) {
    Write-Host "`nGotovo (state-only)."
    exit 0
}

Write-Host "`n[2/3] Provjera RTDE servoJ gibanja (sweep +-5 deg na J5)..."
Invoke-Py @("-m", "src.tools.check_ursim", "--ip", $UrsimIp)

if ($script:LastPyExit -ne 0) {
    Write-Host "`nGreška pri servoJ gibanju! Provjeri Remote Control status u PolyScope-u." -ForegroundColor Red
    exit 1
}

$outDir = Join-Path $script:RepoRoot "testing/lab\results"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$trackPath = Join-Path $outDir "ursim_quicktest.track.csv"
$latPath = Join-Path $outDir "ursim_quicktest.csv"

Write-Host "`n[3/3] Pokretanje testnog 1-DOF replay runa (15 s) s logiranjem kutova..."
Invoke-Py @("-m", "src.pipeline.main",
    "--sink", "ursim", "--ip", $UrsimIp,
    "--seconds", "15",
    "--latency-csv", $latPath,
    "--track-csv", $trackPath,
    "--log-actual")

if (Test-Path $trackPath) {
    Write-Host "`n-> Analiza vjernosti praćenja na simulatoru:`n"
    Invoke-Py @("-m", "src.tools.track_analysis", $trackPath)
}

Write-Host "`n[OK] URSim test uspjesno dovrsen!" -ForegroundColor Green
