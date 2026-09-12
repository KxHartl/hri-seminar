# 02_slobodno_6dof_mock.ps1 -- 6-DOF slobodno gibanje u URSim-u s Mock izvorom
#
# Koristi sinteticki generator kretnji ruke (MockArmSource) koji simulira
# prirodne pokrete: rame yaw/pitch -> J1/J2, lakat -> J3, zapesce -> J4/J5/J6.
# Nije potreban vanjski OptiTrack sustav!
#
# Primjeri koristenja:
#   .\02_slobodno_6dof_mock.ps1                    # Kontinuirano gibanje (prekid s Ctrl-C)
#   .\02_slobodno_6dof_mock.ps1 -Seconds 30        # Trajanje 30 s
#   .\02_slobodno_6dof_mock.ps1 -RangeDps 45       # Povecan dopusteni raspon (+-45 deg)
#   .\02_slobodno_6dof_mock.ps1 -Filter none       # Bez filtriranja (test suma/odziva)

param(
    [string]$UrsimIp        = "192.168.208.128",
    [double]$Seconds        = 0,             # 0 = kontinuirano do Ctrl-C
    [double]$RangeDps       = 90,            # dopusteni +- otklon [deg] po zglobu
    [double]$SpeedDps       = 150,           # maksimalna brzina zgloba [deg/s]
    [string]$Filter         = "one_euro",    # one_euro | butterworth | ema | none
    [double]$DropRate       = 0.0,           # simulirani gubitak paketa [0..1]
    [int]$AddedLatencyMs    = 0,             # umjetno dodano kasnjenje [ms]
    [int]$Port              = 51000,
    [string]$Tag            = "mock6dof",
    [switch]$NoHome
)

. "$PSScriptRoot\_common.ps1"

$outDir = Join-Path $PSScriptRoot "results"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base  = Join-Path $outDir "$Tag`_$stamp"

$durText = if ($Seconds -gt 0) { "$Seconds s" } else { "KONTINUIRANO (zaustavi s Ctrl-C)" }

Write-Head "02 -- 6-DOF SLOBODNO GIBANJE (MOCK -> URSIM)" @{
    "URSim IP"   = $UrsimIp
    "Trajanje"   = $durText
    "Filtar"     = $Filter
    "Granice"    = "+-$RangeDps deg, $SpeedDps deg/s (po zglobu)"
    "Gubitak UDP"= "$($DropRate * 100) %"
    "Dodani lag" = "$AddedLatencyMs ms"
    "Zapis"      = (Split-Path $base -Leaf)
}

if (-not $NoHome) {
    Write-Host "`n[1/3] Postavljam simulator u pocetnu referentnu pozu..."
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $UrsimIp, "--yes")
}

$bridge = $null
try {
    Write-Host "`n[2/3] Pokrecem Mock 6-DOF izvor u pozadini..."
    $bridge = Start-MockBridge -Port $Port

    $timeoutS = if ($AddedLatencyMs -gt 0) { [math]::Max(0.15, ($AddedLatencyMs / 1000.0) + 0.15) } else { 0.15 }

    $pyArgs = @(
        "-m", "src.pipeline.main",
        "--external", "--port", "$Port",
        "--mode", "multi_joint",
        "--sink", "ursim", "--ip", $UrsimIp,
        "--seconds", "$Seconds",
        "--filter", $Filter,
        "--range-dps", "$RangeDps", "--max-speed-dps", "$SpeedDps",
        "--drop-rate", "$DropRate",
        "--added-latency-ms", "$AddedLatencyMs",
        "--signal-timeout-s", "$timeoutS",
        "--latency-csv", "$base.csv",
        "--track-csv", "$base.track.csv", "--log-actual"
    )

    Write-Host "`n[3/3] Pokrecem 6-DOF pipeline prema URSim-u ($durText)...`n"
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
