# 01 — REFERENTNA POZA (home)
#
# Home NIJE robotski home nego poza koja odgovara RAVNOJ ISPRUŽENOJ RUCI:
# [250, -180, 0, 0, 90, 0] deg, zapisano u src/config/default.yaml (robot.home_q_deg).
# Svaki run kreće odavde — inače svaki sljedeći run "homea" ondje gdje je prethodni
# stao pa se dopušteni pojas zgloba pomiče (izmjereno 2026-08-31: lakat 0 -> 20 -> 37 deg).
#
#   .\01_home.ps1              vrati robota u referentnu pozu (pita za potvrdu)
#   .\01_home.ps1 -Capture     spremi TRENUTNU pozu robota kao novu referentnu
#   .\01_home.ps1 -Show        samo ispiši odstupanje, ne miči robota

param(
    [string]$RobotIp = "192.168.40.50",
    [switch]$Capture,
    [switch]$Show,
    [double]$Speed = 0.3          # moveJ brzina [rad/s] — namjerno sporo, ljudi su blizu
)

. "$PSScriptRoot\_common.ps1"

Write-Head "01 — REFERENTNA POZA (ravna ispružena ruka)" @{ Robot = $RobotIp; Brzina = "$Speed rad/s" }

if ($Capture) {
    Write-Host "Spremam trenutnu pozu robota kao referentnu ..."
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--capture")
    exit $script:LastPyExit
}
if ($Show) {
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--show")
    exit $script:LastPyExit
}

Write-Host "ROBOT ĆE SE GIBATI. Prostor mora biti prazan, e-stop u ruci." -ForegroundColor Yellow
Invoke-Py @("-m", "src.tools.home_pose", "--ip", $RobotIp, "--speed", "$Speed")
exit $script:LastPyExit
