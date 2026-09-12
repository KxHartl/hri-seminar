# 00_ursim_provjera.ps1 — Provjera stanja simulatora u VMware-u (bez gibanja)
#
# Provjerava mreznu dostupnost, RTDE receive vezu i trenutno stanje robota u URSim-u.

param(
    [string]$UrsimIp = "192.168.208.128"
)

. "$PSScriptRoot\_common.ps1"

Write-Head "00 — PROVJERA URSIM STANJA (VMware)" @{ "URSim IP" = $UrsimIp; "Mod" = "Samo ocitanje (bez gibanja)" }

Write-Host "`n[1/2] Test ping..."
Test-Connection -ComputerName $UrsimIp -Count 2 | Select-Object Destination, IPV4Address, ResponseTime

Write-Host "`n[2/2] RTDE Receive ocitanje zglobova i stanja..."
Invoke-Py @("-m", "src.tools.check_ursim", "--ip", $UrsimIp, "--no-move")

if ($script:LastPyExit -eq 0) {
    Write-Host "`n[OK] URSim je spreman za simulaciju!" -ForegroundColor Green
} else {
    Write-Host "`n[GRESKA] Provjeri je li URSim upaljen i u Remote Control modu." -ForegroundColor Red
}
exit $script:LastPyExit
