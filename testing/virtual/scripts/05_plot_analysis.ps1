# 05_analiza_grafovi.ps1 -- Ponovna analiza i generiranje grafova za snimljene rezultate
#
# Koristenje:
#   .\05_analiza_grafovi.ps1                                # Analizira zadnji snimljeni .track.csv
#   .\05_analiza_grafovi.ps1 -TrackCsv results\moj_run.track.csv

param(
    [string]$TrackCsv = ""
)

. "$PSScriptRoot\_common.ps1"

if (-not $TrackCsv) {
    $resultsDir = Join-Path $PSScriptRoot "results"
    $latest = Get-ChildItem -Path $resultsDir -Filter "*.track.csv" -Recurse |
              Sort-Object LastWriteTime -Descending |
              Select-Object -First 1

    if (-not $latest) {
        Write-Host "Nema pronadjenih .track.csv datoteka u $resultsDir." -ForegroundColor Yellow
        exit 0
    }
    $TrackCsv = $latest.FullName
} else {
    if (-not (Test-Path $TrackCsv)) {
        $TrackCsv = Join-Path $script:RepoRoot $TrackCsv
    }
}

Write-Head "05 -- ANALIZA VJERNOSTI I GENERIRANJE FIGURA" @{ "Datoteka" = (Split-Path $TrackCsv -Leaf) }

Invoke-Py @("-m", "src.tools.track_analysis", $TrackCsv)

$png = [System.IO.Path]::ChangeExtension($TrackCsv, ".png")
if (Test-Path $png) {
    Write-Host "`nGrafikon generiran:" -ForegroundColor Green
    Write-Host ("  -> " + $png)
}
