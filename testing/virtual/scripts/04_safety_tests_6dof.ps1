# 04_sigurnosni_testovi_6dof.ps1 -- Verifikacija sigurnosnih mehanizama na simulatoru
#
# Provodi 4 kljucna sigurnosna testa u 6-DOF nacinu rada:
# 1. Rate-limit (ogranicenje brzine zglobova)
# 2. Range-limit (radni prostor / maksimalni otklon)
# 3. Softverski E-Stop (trenutno zaustavljanje)
# 4. Fail-safe pri gubitku signala (timeout)

param(
    [string]$UrsimIp = "192.168.208.128",
    [ValidateSet("all", "ratelimit", "rangelimit", "estop", "failsafe")][string]$Test = "all",
    [int]$Port = 51000
)

. "$PSScriptRoot\_common.ps1"

$outDir = Join-Path $PSScriptRoot "results\safety"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Run-SafetyTest([string]$Name, [string[]]$Args, [string]$Desc) {
    Write-Host "`n"
    Write-Host ("-" * 78)
    Write-Host "TEST: $Name -- $Desc"
    Write-Host ("-" * 78)
    
    $trackPath = Join-Path $outDir ($Name + ".track.csv")
    $latPath   = Join-Path $outDir ($Name + ".csv")

    Write-Host "-> Vracam robot u referentnu pozu..."
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $UrsimIp, "--yes")

    $bridge = Start-MockBridge -Port $Port
    try {
        $fullArgs = @(
            "-m", "src.pipeline.main",
            "--external", "--port", "$Port",
            "--mode", "multi_joint",
            "--sink", "ursim", "--ip", $UrsimIp,
            "--latency-csv", $latPath,
            "--track-csv", $trackPath, "--log-actual"
        ) + $Args
        Invoke-Py $fullArgs
    }
    finally {
        Stop-Bridge $bridge
    }

    if (Test-Path $trackPath) {
        Write-Host "`n-> Provjera sigurnosnih zastavica u logu:"
        Invoke-Py @("-m", "src.tools.track_analysis", $trackPath)
    }
}

Write-Head "04 -- SIGURNOSNI TESTOVI 6-DOF (URSIM)" @{ "URSim IP" = $UrsimIp; "Odabrani test" = $Test }

if ($Test -eq "all" -or $Test -eq "ratelimit") {
    Run-SafetyTest "sec_01_ratelimit" @("--seconds", "15", "--max-speed-dps", "10", "--range-dps", "45") `
                   "Ogranicenje brzine zgloba (max 10 deg/s)"
}

if ($Test -eq "all" -or $Test -eq "rangelimit") {
    Run-SafetyTest "sec_02_rangelimit" @("--seconds", "15", "--range-dps", "15", "--max-speed-dps", "40") `
                   "Ogranicenje raspona kretanja (+-15 deg oko home)"
}

if ($Test -eq "all" -or $Test -eq "estop") {
    Run-SafetyTest "sec_03_estop" @("--seconds", "20", "--estop-after", "8") `
                   "Softverski E-Stop nakon 8 sekundi rada"
}

if ($Test -eq "all" -or $Test -eq "failsafe") {
    Write-Host "`n"
    Write-Host ("-" * 78)
    Write-Host "TEST: sec_04_failsafe -- Simulirani prekid signala i timeout"
    Write-Host ("-" * 78)
    $trackPath = Join-Path $outDir "sec_04_failsafe.track.csv"
    $latPath   = Join-Path $outDir "sec_04_failsafe.csv"

    # Pokreni bridge, pa ugasi nakon 5 s
    $bridge = Start-MockBridge -Port $Port
    $job = Start-Job -ScriptBlock {
        param($PID_TO_KILL)
        Start-Sleep -Seconds 6
        Stop-Process -Id $PID_TO_KILL -Force -ErrorAction SilentlyContinue
    } -ArgumentList $bridge.Id

    try {
        Invoke-Py @(
            "-m", "src.pipeline.main",
            "--external", "--port", "$Port",
            "--mode", "multi_joint",
            "--sink", "ursim", "--ip", $UrsimIp,
            "--seconds", "15",
            "--signal-timeout-s", "0.15",
            "--latency-csv", $latPath,
            "--track-csv", $trackPath, "--log-actual"
        )
    }
    finally {
        Stop-Bridge $bridge
        Remove-Job $job -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $trackPath) {
        Invoke-Py @("-m", "src.tools.track_analysis", $trackPath)
    }
}

Write-Host "`n[OK] Sigurnosni testovi zavrseni! Rezultati su u $outDir" -ForegroundColor Green
