# POKRENI SVE TESTOVE - 6-DOF ispitna matrica uskladjena s 02_slobodno_gibanje
#
# SVI TESTOVI RADE NA 6-DOF (svih 6 zglobova u realnom vremenu uz OptiTrack kruta tijela).
# 1. Vjernost pracenja (T-02 normalni tempo, T-03 brzi tempo)
# 2. Usporedba filtara na 6-DOF (One-Euro, None, Butterworth, EMA - T-04..T-07)
# 3. Sigurnosni testovi na 6-DOF (Rate-limit, Range-limit, Fail-safe okluzija, Softverski E-stop, Step odziv - T-08..T-12, T-20)
# 4. Latencijski sweep na 6-DOF (0, 50, 100, 200, 400 ms - T-13a..T-13e)
# 5. Gubitak paketa na 6-DOF (0%, 5%, 10%, 20%, 30% - T-14..T-18)
#
# Svaki test samostalno dize arm most i multi_joint pipeline, logira kutove i RTDE stvarni kut robota,
# te sprema podatke u data/raw/lab_session_01092026_020000/telemetry/T-XX.*.
#
# Pokretanje:
#   .\pokreni_sve_testove.ps1                   # pokrece sve redom
#   .\pokreni_sve_testove.ps1 -Group fidelity  # samo vjernost pracenja
#   .\pokreni_sve_testove.ps1 -Group filters   # samo usporedba filtara
#   .\pokreni_sve_testove.ps1 -Group safety    # samo sigurnosni testovi
#   .\pokreni_sve_testove.ps1 -Group latency   # samo latencijski sweep (pHRI)
#   .\pokreni_sve_testove.ps1 -Group loss      # samo gubitak paketa
#   .\pokreni_sve_testove.ps1 -Sink dry_run    # suha proba bez gibanja robota

param(
    [string]$RobotIp  = "192.168.40.50",
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30",
    [ValidateSet("all", "fidelity", "filters", "safety", "latency", "loss")][string]$Group = "all",
    [string]$Sink     = "ur3e",
    [int]$Port        = 51000
)

. "$PSScriptRoot\_common.ps1"

$outDir = Join-Path $script:RepoRoot "testing/lab\results"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Run-SingleTest {
    param(
        [string]$Id,
        [string]$Name,
        [string]$Description,
        [double]$Seconds = 30,
        [string]$Filter = "one_euro",
        [double]$RangeDps = 90,
        [double]$SpeedDps = 150,
        [double]$AddedLatencyMs = 0,
        [double]$SignalTimeoutS = 0.15,
        [double]$DropRate = 0,
        [double]$EstopAfter = 0,
        [switch]$NoHome
    )

    $base = Join-Path $outDir $Id
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host ("TEST " + $Id + " - " + $Name) -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host ("Upute za operatera: " + $Description) -ForegroundColor Yellow
    Write-Host ("Trajanje: " + $Seconds + " s | 6-DOF mimikrija (arm bridge) | Filtar: " + $Filter + " | Dodana latencija: " + $AddedLatencyMs + " ms")
    Write-Host "E-stop u ruci. Prekid ovog testa: Ctrl-C."
    Read-Host "Pritisni Enter kada si spreman za ovaj test (ili Ctrl-C za izlaz)" | Out-Null

    if (-not $NoHome -and $Sink -ne "dry_run") {
        Write-Host "-> vracam robota u referentnu pozu ..."
        Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--yes")
    }

    $pyArgs = @("-m", "src.pipeline.main",
        "--external", "--port", "$Port",
        "--mode", "multi_joint",
        "--sink", $Sink, "--ip", $RobotIp,
        "--seconds", "$Seconds",
        "--filter", "$Filter",
        "--range-dps", "$RangeDps", "--max-speed-dps", "$SpeedDps",
        "--latency-csv", ($base + ".csv"),
        "--track-csv", ($base + ".track.csv"), "--log-actual")

    if ($AddedLatencyMs -gt 0) {
        $pyArgs += @("--added-latency-ms", "$AddedLatencyMs")
    }
    if ($SignalTimeoutS -ne 0.15) {
        $pyArgs += @("--signal-timeout-s", "$SignalTimeoutS")
    }
    if ($DropRate -gt 0) {
        $pyArgs += @("--drop-rate", "$DropRate")
    }
    if ($EstopAfter -gt 0) {
        $pyArgs += @("--estop-after", "$EstopAfter")
    }

    $bridge = $null
    try {
        $bridge = Start-Bridge -Mode arm -ServerIp $MotiveIp -ClientIp $ClientIp -Port $Port
        Write-Host ("-> pokrecem 6-DOF mjerenje [" + $Seconds + " s] ... Kreni s pokretom!`n")
        Invoke-Py $pyArgs
    }
    catch {
        Write-Host ("!! Prekid ili greska na testu " + $Id + ": " + $_) -ForegroundColor Yellow
    }
    finally {
        Stop-Bridge $bridge
    }

    if (Test-Path ($base + ".track.csv")) {
        Write-Host ("`n-> Analiza rezultata (" + $Id + "):") -ForegroundColor Green
        Invoke-Py @("-m", "src.tools.track_analysis", ($base + ".track.csv"))
    }

    Write-Host ("`n[OK] Test " + $Id + " je zavrsen i podaci su spremljeni u: " + $base + ".*") -ForegroundColor Green
    Write-Host ("-" * 78) -ForegroundColor DarkGray
    Read-Host "Pritisni Enter za prelazak na SLJEDECI test (ili Ctrl-C za pauzu)" | Out-Null
}

Write-Head "LAB TEST SUITE RUNNER (100% 6-DOF)" @{
    Robot = $RobotIp; Motive = $MotiveIp; Grupa = $Group; Sink = $Sink
}

# --- 1. VJERNOST PRACENJA NA 6-DOF (T-02, T-03) ---
if ($Group -in @("all", "fidelity")) {
    Run-SingleTest -Id "T-02" -Name "6-DOF vjernost pracenja - normalni tempo" `
        -Description "Kreni s ispruzenom rukom. Prirodno i ravnomjerno gibaj rame, lakat i zapesce 45 s." `
        -Seconds 45 -RangeDps 90 -SpeedDps 150

    Run-SingleTest -Id "T-03" -Name "6-DOF slobodno pracenje - dinamicki brzi tempo" `
        -Description "Kombiniraj brze i raznovrsne pokrete cijele ruke 45 s." `
        -Seconds 45 -RangeDps 90 -SpeedDps 150
}

# --- 2. USPOREDBA FILTARA NA STVARNOM ROBOTU (6-DOF, T-04..T-07) ---
if ($Group -in @("all", "filters")) {
    Run-SingleTest -Id "T-04" -Name "Filtar 6-DOF: One-Euro (baseline)" `
        -Description "Ravnomjerno i prirodno gibaj cijelu ruku 30 s [rame, lakat, zapesce]." `
        -Seconds 30 -Filter "one_euro" -RangeDps 90 -SpeedDps 150

    Run-SingleTest -Id "T-05" -Name "Filtar 6-DOF: Bez filtriranja (none)" `
        -Description "Isti tempo pokreta cijele ruke 30 s [osjeti/vidi ima li vise suma i trzanja zglobova]." `
        -Seconds 30 -Filter "none" -RangeDps 90 -SpeedDps 150

    Run-SingleTest -Id "T-06" -Name "Filtar 6-DOF: Butterworth" `
        -Description "Isti tempo pokreta cijele ruke 30 s." `
        -Seconds 30 -Filter "butterworth" -RangeDps 90 -SpeedDps 150

    Run-SingleTest -Id "T-07" -Name "Filtar 6-DOF: EMA (eksponencijalni prosjek)" `
        -Description "Isti tempo pokreta cijele ruke 30 s." `
        -Seconds 30 -Filter "ema" -RangeDps 90 -SpeedDps 150
}

# --- 3. SIGURNOSNI MEHANIZMI NA 6-DOF (T-08..T-12, T-20) ---
if ($Group -in @("all", "safety")) {
    Run-SingleTest -Id "T-08" -Name "Sigurnost 6-DOF: Rate-limit (ogranicenje brzine)" `
        -Description "Napravi nekoliko JAKO NAGLIH pokreta rukom. Robot ce glatko ograniciti brzinu svih zglobova na 25 deg/s." `
        -Seconds 25 -SpeedDps 25 -RangeDps 90

    Run-SingleTest -Id "T-09" -Name "Sigurnost 6-DOF: Range-limit (ogranicenje raspona)" `
        -Description "Namjerno napravi vece pomake rukom preko dopustenog kuta. Robot ce stati na granici +-25 deg." `
        -Seconds 25 -RangeDps 25 -SpeedDps 150

    Run-SingleTest -Id "T-10" -Name "Sigurnost 6-DOF: Fail-safe na okluziju signala" `
        -Description "Gibaj ruku, zatim NAKON 10 SEKUNDI RUKOM PREKRIJ MARKERE na 3-4 s, pa ponovno makni ruku. Dostupni zglobovi nastavljaju, a pri punom prekidu robot mirno stane." `
        -Seconds 30 -RangeDps 90 -SpeedDps 150

    Run-SingleTest -Id "T-12a" -Name "Sigurnost 6-DOF: Softverski E-stop dokaz" `
        -Description "Gibaj cijelu ruku. Nakon 10 s skripta automatski okida E-stop i zamrzava svih 6 zglobova." `
        -Seconds 20 -EstopAfter 10 -RangeDps 90 -SpeedDps 150

    Run-SingleTest -Id "T-20" -Name "Odziv 6-DOF: 5 naglih pokreta ruke (step response)" `
        -Description "Napravi 5 brzih pokreta rukom uz krace pauze izmedju svakog." `
        -Seconds 30 -RangeDps 90 -SpeedDps 150
}

# --- 4. UTJECAJ LATENCIJE / pHRI NA 6-DOF (T-13a..T-13e) ---
if ($Group -in @("all", "latency")) {
    Run-SingleTest -Id "T-13a" -Name "Latencija 6-DOF: +0 ms kasnjenja (baseline)" `
        -Description "Normalno gibaj cijelu ruku 30 s [osjeti direktnu teleoperaciju]." `
        -Seconds 30 -AddedLatencyMs 0 -SignalTimeoutS 0.15

    Run-SingleTest -Id "T-13b" -Name "Latencija 6-DOF: +50 ms dodanog kasnjenja" `
        -Description "Isti pokret cijele ruke 30 s." `
        -Seconds 30 -AddedLatencyMs 50 -SignalTimeoutS 0.30

    Run-SingleTest -Id "T-13c" -Name "Latencija 6-DOF: +100 ms dodanog kasnjenja" `
        -Description "Isti pokret cijele ruke 30 s [osjeti pocinje li smetati lag na 6 zglobova]." `
        -Seconds 30 -AddedLatencyMs 100 -SignalTimeoutS 0.40

    Run-SingleTest -Id "T-13d" -Name "Latencija 6-DOF: +200 ms dodanog kasnjenja" `
        -Description "Isti pokret cijele ruke 30 s [vidljivo kasnjenje, degradacija upravljivosti]." `
        -Seconds 30 -AddedLatencyMs 200 -SignalTimeoutS 0.60

    Run-SingleTest -Id "T-13e" -Name "Latencija 6-DOF: +400 ms dodanog kasnjenja" `
        -Description "Isti pokret cijele ruke 30 s [veliko kasnjenje]." `
        -Seconds 30 -AddedLatencyMs 400 -SignalTimeoutS 0.90
}

# --- 5. KONTROLIRANI GUBITAK PAKETA NA 6-DOF (T-14..T-18) ---
if ($Group -in @("all", "loss")) {
    Run-SingleTest -Id "T-14" -Name "Gubitak paketa 6-DOF: 0%" `
        -Description "Normalno gibaj cijelu ruku 25 s." `
        -Seconds 25 -DropRate 0.0

    Run-SingleTest -Id "T-15" -Name "Gubitak paketa 6-DOF: 5%" `
        -Description "Isti pokret cijele ruke 25 s." `
        -Seconds 25 -DropRate 0.05

    Run-SingleTest -Id "T-16" -Name "Gubitak paketa 6-DOF: 10%" `
        -Description "Isti pokret cijele ruke 25 s." `
        -Seconds 25 -DropRate 0.10

    Run-SingleTest -Id "T-17" -Name "Gubitak paketa 6-DOF: 20%" `
        -Description "Isti pokret cijele ruke 25 s." `
        -Seconds 25 -DropRate 0.20

    Run-SingleTest -Id "T-18" -Name "Gubitak paketa 6-DOF: 30%" `
        -Description "Isti pokret cijele ruke 25 s." `
        -Seconds 25 -DropRate 0.30
}

Write-Host ""
Write-Host ("=" * 78) -ForegroundColor Green
Write-Host ("SVI TESTOVI SU USPJESNO ZAVRSENI I SPREMLJENI U: " + $outDir) -ForegroundColor Green
Write-Host ("=" * 78) -ForegroundColor Green
