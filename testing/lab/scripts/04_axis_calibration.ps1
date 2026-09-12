# 04 — KALIBRACIJA OSI (arm_axes) — obavezno prije 6-DOF, robot se NE giba
#
# Euler seq/indeks/predznak po segmentu ovise o tome kako su definirane lokalne osi
# krutih tijela u Motiveu. Kad se tijela naprave iznova (a 2026-08-31 su im se
# promijenili stream ID-evi, što na to upućuje), lipanjska kalibracija ne vrijedi.
#
# Postupak (alat ti sam ispisuje): drži ISPRUŽENU ruku dok se ne javi "HOME postavljen",
# pa radi JEDAN izolirani pokret po jedan i gledaj koja RAW komponenta reagira:
#   1) rame gore/dolje   2) rame lijevo/desno   3) lakat
#   4) šaka gore/dolje   5) šaka lijevo/desno   6) pronacija/supinacija podlaktice
# Nađene vrijednosti upiši u src/config/default.yaml -> arm_axes, pa pokreni ponovo i
# provjeri da MAPPED kanali reagiraju svaki na svoj pokret.
#
#   .\04_kalibracija_osi.ps1        # Ctrl-C za izlaz

param(
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30"
)

. "$PSScriptRoot\_common.ps1"

Write-Head "04 — KALIBRACIJA OSI (arm_inspect, bez robota)" @{ Motive = $MotiveIp; PC = $ClientIp }

Write-Host "`nRobot se NE giba. Izađi s Ctrl-C kad pokupiš sve komponente.`n"
Invoke-Py @("$($script:RepoRoot)\testing/lab\diag\arm_inspect.py", $MotiveIp, $ClientIp)
