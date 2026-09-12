# 03 — HOD PO ZGLOBOVIMA (korak po korak, zglob po zglob)
#
# Vodi te kroz svih šest zglobova, jedan po jedan: terminal ispisuje što raditi
# (jedna uputa u sekundi, pa odbrojavanje 3-2-1), robot se između koraka vraća u
# referentnu pozu, a nakon svakog koraka dobiješ izmjerene brojke za taj zglob
# (raspon ulaza, raspon naredbe, naredba->stvarno RMSE i lag, koliko je clamp okidao).
#
# Ulaz je uvijek KUT LAKTA (most --sdk); mijenja se zglob robota koji taj kut vozi,
# pa provjeravaš svaki zglob posebno: miče li se, u kojem smjeru i koliko vjerno.
#
#   .\03_hod_po_zglobovima.ps1                    # svih 6, 12 s po zglobu
#   .\03_hod_po_zglobovima.ps1 -Joints "2,3" -Seconds 20
#   .\03_hod_po_zglobovima.ps1 -Sink dry_run      # proba bez gibanja robota

param(
    [string]$RobotIp  = "192.168.40.50",
    [string]$MotiveIp = "192.168.40.31",
    [string]$ClientIp = "192.168.40.30",
    [string]$Joints   = "0,1,2,3,4,5",   # 0-based (0=baza ... 5=zapešće 3)
    [double]$Seconds  = 12,
    [string]$Sink     = "ur3e",          # dry_run = proba, robot se ne miče
    [double]$RangeDps = 0,               # 0 = per-zglob default iz alata
    [double]$SpeedDps = 0,
    [int]$Port        = 51000
)

. "$PSScriptRoot\_common.ps1"

Write-Head "03 — HOD PO ZGLOBOVIMA" @{
    Robot = $RobotIp; Zglobovi = $Joints; PoZglobu = "$Seconds s"; Sink = $Sink
}

if ($Sink -ne "dry_run") {
    Write-Host "`nROBOT ĆE SE GIBATI, zglob po zglob, uz povratak u referentnu pozu." -ForegroundColor Yellow
    Write-Host "Nitko u radnom prostoru. E-stop u ruci. Prekid: Ctrl-C." -ForegroundColor Yellow
    Read-Host "Enter za nastavak (Ctrl-C za odustajanje)" | Out-Null
}

$cliArgs = @("-m", "src.tools.joint_walkthrough", "--ip", $RobotIp, "--port", "$Port",
          "--sink", $Sink, "--joints", $Joints, "--seconds", "$Seconds")
if ($RangeDps -gt 0) { $cliArgs += @("--range-dps", "$RangeDps") }
if ($SpeedDps -gt 0) { $cliArgs += @("--max-speed-dps", "$SpeedDps") }

$bridge = $null
try {
    $bridge = Start-Bridge -Mode sdk -ServerIp $MotiveIp -ClientIp $ClientIp -Port $Port
    Invoke-Py $cliArgs
}
finally {
    Stop-Bridge $bridge
}

Write-Host "`nZapisi: testing/lab\results\walkthrough\J*.track.csv (+ .png figure)"
