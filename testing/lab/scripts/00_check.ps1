# 00 — PROVJERA (ništa se ne miče)
#
# Pokreni prvu stvar u labosu i nakon svake promjene mreže/Motivea.
# Provjerava: okruženje, robota (RTDE stanje), Motive stream i kruta tijela.

param(
    [string]$RobotIp  = "192.168.40.50",
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30"
)

. "$PSScriptRoot\_common.ps1"

Write-Head "00 — PROVJERA (bez gibanja)" @{ Robot = $RobotIp; Motive = $MotiveIp; PC = $ClientIp }

Write-Host "`n[1/4] Preflight (paketi, SDK, config, dokumenti, ping) ..."
Invoke-Py @("-m", "src.tools.preflight", "--robot", $RobotIp, "--motive", $MotiveIp)

Write-Host "`n[2/4] Robot — RTDE stanje (bez gibanja) ..."
Invoke-Py @("-m", "src.tools.check_ursim", "--ip", $RobotIp, "--no-move")

Write-Host "`n[3/4] Referentna poza — gdje je robot u odnosu na home ..."
Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--show")

Write-Host "`n[4/4] Motive — veza i broj okvira ..."
Invoke-Py @("testing/lab\diag\sdk_probe.py", $MotiveIp, $ClientIp, "0") 6>&1 |
    Select-String -Pattern "connected|application|MotiveVer|NatNetVer|frames" | ForEach-Object { "  $_" }

Write-Host "`nGotovo. Ako je sve OK: 01_home.ps1 pa 02_slobodno_gibanje.ps1."
