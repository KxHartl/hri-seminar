# 03_slobodno_6dof_live.ps1 -- 6-DOF slobodno gibanje u URSim-u s pravim Motive izvorom
#
# Koristi zivi NatNet stream iz OptiTrack Motivea (3 rigid bodyja) i preslikava
# pokrete covjeka na svih 6 zglobova simulatora u realnom vremenu.

param(
    [string]$UrsimIp  = "192.168.208.128",
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30",
    [double]$Seconds  = 0,             # 0 = kontinuirano do Ctrl-C
    [double]$RangeDps = 90,            # dopusteni +- otklon [deg] po zglobu
    [double]$SpeedDps = 150,           # maksimalna brzina zgloba [deg/s]
    [string]$Filter   = "one_euro",
    [int]$Port        = 51000,
    [string]$Tag      = "live6dof_ursim",
    [switch]$NoHome
)

. "$PSScriptRoot\_common.ps1"

$outDir = Join-Path $PSScriptRoot "results"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base  = Join-Path $outDir "$Tag`_$stamp"

$durText = if ($Seconds -gt 0) { "$Seconds s" } else { "KONTINUIRANO (zaustavi s Ctrl-C)" }

Write-Head "03 -- 6-DOF SLOBODNO GIBANJE (ZIVI MOTIVE -> URSIM)" @{
    "URSim IP"   = $UrsimIp
    "Motive IP"  = $MotiveIp
    "Lokalni IP" = $ClientIp
    "Trajanje"   = $durText
    "Granice"    = "+-$RangeDps deg, $SpeedDps deg/s (po zglobu)"
    "Zapis"      = (Split-Path $base -Leaf)
}

if (-not $NoHome) {
    Write-Host "`n[1/3] Postavljam simulator u pocetnu referentnu pozu..."
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $UrsimIp, "--yes")
}

$bridge = $null
try {
    Write-Host "`n[2/3] Pokrecem zivi 6-DOF NatNet bridge prema Motiveu..."
    $bridge = Start-LiveBridge -ServerIp $MotiveIp -ClientIp $ClientIp -Port $Port

    $pyArgs = @(
        "-m", "src.pipeline.main",
        "--external", "--port", "$Port",
        "--mode", "multi_joint",
        "--sink", "ursim", "--ip", $UrsimIp,
        "--seconds", "$Seconds",
        "--filter", $Filter,
        "--range-dps", "$RangeDps", "--max-speed-dps", "$SpeedDps",
        "--latency-csv", "$base.csv",
        "--track-csv", "$base.track.csv", "--log-actual"
    )

    Write-Host "`n[3/3] Pokrecem 6-DOF pipeline prema URSim-u ($durText)...`n"
    Write-Host "Kreni s ISPRUZENOM rukom. Pomici ruku u volumenu Motivea.`n" -ForegroundColor Yellow
    Invoke-Py $pyArgs
}
finally {
    Stop-Bridge $bridge
}

if (Test-Path "$base.track.csv") {
    Write-Host "`n=============================================================================="
    Write-Host "ANALIZA REZULTATA PO ZGLOBOVIMA (J1-J6):"
    Write-Host "=============================================================================="
    Invoke-Py @("-m", "src.tools.track_analysis", "$base.track.csv")
}

Write-Host "`n[OK] Zapisano u:"
Write-Host ("  -> CSV:     " + $base + ".track.csv")
Write-Host ("  -> Figura:  " + $base + ".track.png")
Write-Host ("  -> Vrijeme: " + $base + ".summary.json")
