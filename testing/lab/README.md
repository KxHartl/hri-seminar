# testing/lab — testiranje na stvarnom robotu (UR3e + OptiTrack)

Sve što je potrebno za provođenje mjerenja u laboratoriju: protokoli, izvršne skripte,
dijagnostika živog OptiTrack puta i obrasci za zapisivanje.

> **Status:** sesija je provedena **1.–2. 9. 2026.** Prikupljeni podaci i rezultati
> nalaze se u [`data/raw/lab_session_01092026_020000/`](../../data/raw/lab_session_01092026_020000/),
> a pregled svih pokusa u [glavnom README-u](../../README.md) (§7).
> Ovaj direktorij dokumentira **kako** su podaci prikupljeni.

## ⚠️ Sigurnost prije svega

- **Prvi pokreti uvijek bez čovjeka u radnom prostoru robota.**
- **Hardverski e-stop na dohvat ruke i testiran prije svakog runa.**
- Kreni s **konzervativnim granicama** (`src/config/default.yaml` → `safety`), pa postupno otpuštaj.
- Snimke imaju velik raspon fleksije (do ~95°) → zglob **J3 (lakat)** se stvarno i brzo giba.

## Hardver (stanje od 2026-08-31)

| Uloga | Uređaj | IP |
|---|---|---|
| Robot | **UR3e**, PolyScope 5.9.5 — **traži „Remote Control" mod** | `192.168.40.50` |
| Mocap | Motive 3.0.1 / NatNet 4.0, **unicast** | `192.168.40.31` |
| Upravljačko računalo | ovaj PC | `192.168.40.30` |

Raniji robot bio je UR3/CB3 na `.27`, gdje „Remote Control" mod ne postoji.
Detalji mreže i potvrđene Motive postavke: [`diag/README.md`](diag/README.md).

## Struktura direktorija

```
testing/lab/
├── protocols/   → protokoli i runbookovi (što raditi, kojim redom)
├── scripts/     → PowerShell skripte koje se stvarno pokreću
├── diag/        → dijagnostika živog NatNet/Motive puta
└── templates/   → obrasci za zapisivanje tijekom sesije
```

### `protocols/` — protokoli sesije

| Datoteka | Svrha |
|---|---|
| [`01_preflight.md`](protocols/01_preflight.md) | Što pripremiti i potvrditi **prije** dolaska u labos |
| [`02_setup.md`](protocols/02_setup.md) | Postavljanje u labosu: robot, mreža, Motive |
| [`03_test_protocol.md`](protocols/03_test_protocol.md) | Opće smjernice za izvođenje pojedinog testa |
| [`04_data_collection.md`](protocols/04_data_collection.md) | Što snimiti i spremiti, imenovanje, mapiranje na sekcije rada |
| [`05_troubleshooting.md`](protocols/05_troubleshooting.md) | Česti problemi i brza rješenja |
| [`06_live_optitrack.md`](protocols/06_live_optitrack.md) | Živi NatNet stream: zašto preko SDK-a i kako se pokreće |
| [`07_demo_runbook.md`](protocols/07_demo_runbook.md) | **Runbook za živu demonstraciju** pred profesorom |
| [`08_session_plan.md`](protocols/08_session_plan.md) | **Matrica pokusa T-01…T-21** — glavni protokol provedene sesije |
| [`08_future_test_proposals.md`](protocols/08_future_test_proposals.md) | Prijedlozi pokusa koji nisu provedeni |
| [`09_motive_setup.md`](protocols/09_motive_setup.md) | Motive: streaming, kruta tijela (ID 25/24/16), kalibracija `arm_axes` |
| [`10_subjective_evaluation.md`](protocols/10_subjective_evaluation.md) | **Popunjeni rezultati** subjektivne pHRI evaluacije (sesija 1.–2. 9. 2026.) |
| [`cheatsheet.md`](protocols/cheatsheet.md) | Jednostranični copy-paste šalabahter (drži otvoreno u labosu) |

### `scripts/` — izvršne skripte

Detaljan opis svake skripte, parametri i redoslijed: [`scripts/README.md`](scripts/README.md).

| Skripta | Robot se giba? | Što radi |
|---|:---:|---|
| [`00_check.ps1`](scripts/00_check.ps1) | ne | Preflight: RTDE stanje, odstupanje od referentne poze, Motive stream |
| [`01_home.ps1`](scripts/01_home.ps1) | **da** | Vraćanje u referentnu pozu ravne ruke |
| [`02_free_motion.ps1`](scripts/02_free_motion.ps1) | **da** | Slobodno gibanje, 6-DOF (ili 1-DOF uz `-Joint`) |
| [`03_joint_walkthrough.ps1`](scripts/03_joint_walkthrough.ps1) | **da** | Vođeni prolaz zglob po zglobu |
| [`04_axis_calibration.ps1`](scripts/04_axis_calibration.ps1) | ne | Kalibracija `arm_axes` prije 6-DOF rada |
| [`05_free_6dof.ps1`](scripts/05_free_6dof.ps1) | **da** | Cijela ruka → svih 6 zglobova, konzervativne granice |
| [`run_all_tests.ps1`](scripts/run_all_tests.ps1) | **da** | **Cijela ispitna matrica** — vodi kroz sve testove i automatski sprema podatke |

### `diag/` — dijagnostika živog puta

`sdk_probe.py`, `natnet_unicast_probe.py`, `sdk_inspect.py`, `arm_inspect.py` —
opis i primjeri pokretanja u [`diag/README.md`](diag/README.md).

### `templates/` — obrasci

| Datoteka | Svrha |
|---|---|
| [`run_log.csv`](templates/run_log.csv) | Predložak dnevnika runova (popunjena verzija: [`data/raw/lab_session_01092026_020000/telemetry/run_log.csv`](../../data/raw/lab_session_01092026_020000/telemetry/run_log.csv)) |
| [`results_tables.md`](templates/results_tables.md) | Predložak tablica rezultata za rad |
| [`safety_signoff.md`](templates/safety_signoff.md) | Sigurnosni checklist po sesiji (potpisuje se) |
| [`phri_questionnaire.md`](templates/phri_questionnaire.md) | Prazan pHRI upitnik (1–7 Likert) — **popunjeni odgovori** su u [`protocols/10_subjective_evaluation.md`](protocols/10_subjective_evaluation.md) |

## Što se prikupljalo i gdje to ulazi u rad

| Mjerenje | Ulazi u |
|---|---|
| Latencija i jitter (`.csv` + `.summary.json` po runu) | Rezultati, Rasprava |
| Vjernost praćenja (`.track.csv`: ulaz, filtrirano, naredba, stvarni kut) | Rezultati |
| Usporedba filtara (One-Euro / Butterworth / EMA / bez filtra) | Metodologija, Rezultati |
| Robusnost (gubitak paketa, fail-safe pri okluziji, e-stop) | Rezultati, Sigurnost |
| Osjetljivost na nagle pokrete (step / trzaj) | Rezultati |
| Subjektivna pHRI evaluacija | Rasprava |
| Fotografije i snimke postava | Slike u radu |

## Gdje završavaju podaci

Skripte tijekom rada zapisuju u **`testing/lab/results/`** (direktorij se stvara pri
prvom pokretanju i nije u gitu). Nakon provedene sesije podaci su arhivirani u
`data/raw/`, pa se **rezultati opisani u radu traže ondje**:

```
data/raw/lab_session_01092026_020000/
├── telemetry/          ← .csv, .track.csv, .summary.json, .track.png po runu
│   ├── run_log.csv     ← zbirna tablica svih runova
│   ├── media_catalog.md← preslikavanje javnih oznaka (T1a…) na interne (T-02…)
│   ├── exploratory/    ← runovi prije službene matrice
│   └── contact_check/  ← prva provjera kontakta s robotom
├── optitrack/          ← Motive .tak snimke i .mkv snimke zaslona
└── photos/             ← fotografije postava, markera i robota
```

Analiza pojedinog zapisa:

```powershell
.venv\Scripts\python -m src.tools.track_analysis <put_do>.track.csv
```
