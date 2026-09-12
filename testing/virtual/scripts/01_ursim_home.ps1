# 01_ursim_home.ps1 — Povratak simulatora u kanonsku referentnu pozu (ravna ruka)
#
# Referentna poza: [250, -180, 0, 0, 90, 0] deg (definirano u src/config/default.yaml)

param(
    [string]$UrsimIp = "192.168.208.128",
    [double]$Speed   = 0.5,
    [switch]$Show,
    [switch]$Yes
)

. "$PSScriptRoot\_common.ps1"

Write-Head "01 — REFERENTNA POZA URSIM (Ravna ispruzena ruka)" @{ "URSim IP" = $UrsimIp; "Brzina" = "$Speed rad/s" }

if ($Show) {
    Invoke-Py @("-m", "src.tools.home_pose", "--ip", $UrsimIp, "--show")
    exit $script:LastPyExit
}

$pyArgs = @("-m", "src.tools.home_pose", "--ip", $UrsimIp, "--speed", "$Speed")
if ($Yes) {
    $pyArgs += "--yes"
}

Invoke-Py $pyArgs
exit $script:LastPyExit
