# Upravljanje zglobom Universal Robots robota pomoću OptiTrack sustava u realnom vremenu

**Autor:** Krešimir Hartl ([kh239762@fsb.hr](mailto:kh239762@fsb.hr))
**Kolegij:** Interakcija čovjeka i robota · Fakultet strojarstva i brodogradnje, Sveučilište u Zagrebu

Sustav koji u realnom vremenu (125 Hz) prati pokret ljudske ruke OptiTrack sustavom
i preslikava ga na zglobove kolaborativnog robota Universal Robots UR3e.

> ## 📄 SEMINARSKI RAD: [**`dist/v1/HRI_seminar_Kresimir_Hartl.pdf`**](dist/v1/HRI_seminar_Kresimir_Hartl.pdf)
>
> 12 stranica · jedina i konačna verzija rada. Sve ostalo u repozitoriju je
> popratni materijal (kod, podaci, snimke pokusa, prezentacija).

---

## 1. Za pregled rada — počni ovdje

Sve je već u repozitoriju. **Ništa se ne mora kompilirati ni pokretati** da bi se rad pregledao.

| # | Što | Gdje |
|:---:|---|---|
| 1 | **Seminarski rad (PDF, 12/12 str.)** | [`dist/v1/HRI_seminar_Kresimir_Hartl.pdf`](dist/v1/HRI_seminar_Kresimir_Hartl.pdf) |
| 2 | **Prezentacija za obranu (17 slajdova)** | [`docs/presentation/hri_presentation.pdf`](docs/presentation/hri_presentation.pdf) |
| 3 | **Video dokazi — 21 pokus na robotu** | [`data/processed/video_clips_01092026/camera/`](data/processed/video_clips_01092026/camera/) (vanjska kamera) i [`optitrack_screen/`](data/processed/video_clips_01092026/optitrack_screen/) (Motive 3D prikaz) |
| 4 | **Mjerenja svih pokusa u jednoj tablici** | [`data/raw/lab_session_01092026_020000/telemetry/run_log.csv`](data/raw/lab_session_01092026_020000/telemetry/run_log.csv) |
| 5 | **Subjektivna pHRI evaluacija (popunjena)** | [`testing/lab/protocols/10_subjective_evaluation.md`](testing/lab/protocols/10_subjective_evaluation.md) |
| 6 | **Razrada svake brojke iz rada** | [`docs/ANALIZA_REZULTATA_I_METRIKA.md`](docs/ANALIZA_REZULTATA_I_METRIKA.md) |
| 7 | **Samorecenzija prije predaje** | [`docs/REVIEW.md`](docs/REVIEW.md) |
| 8 | **Literatura (13 PDF-ova)** | [`data/sources/`](data/sources/) + popis s DOI-jima u [`data/SOURCES_LOG.md`](data/SOURCES_LOG.md) |
| 9 | **Izvorni kod sustava** | [`src/`](src/) — opis u [`src/README.md`](src/README.md) |
| 10 | **Tekst zadatka kolegija** | [`TASK/TASK.md`](TASK/TASK.md) |

> **Veličina repozitorija:** radna kopija je ≈ 1,1 GB (od toga ≈ 0,5 GB videozapisa pokusa
> i ≈ 0,5 GB sirovih snimaka), a s poviješću ≈ 6 GB. Prije kloniranja pokrenuti
> `git lfs install` — bez toga literatura (`data/sources/*.pdf`) i `.pptx` stižu
> samo kao pokazivači, a ne kao datoteke.

---

## 2. Gdje je ispunjen koji zahtjev kolegija

Zahtjevi su preuzeti iz [`TASK/TASK.md`](TASK/TASK.md) (§A *Predaja*, §H *Checklist predaje*).

| Zahtjev kolegija | Ispunjeno — gdje pogledati |
|---|---|
| Tehnički izvještaj u formi znanstvenog rada, **max 12 stranica** | [`dist/v1/HRI_seminar_Kresimir_Hartl.pdf`](dist/v1/HRI_seminar_Kresimir_Hartl.pdf) — **12/12** stranica (build ispisuje `Stranice: N / 12`) |
| Struktura znanstvenog rada (Sažetak → … → Zaključak) | [`docs/chapters/`](docs/chapters/): `00-sazetak` → `01-uvod` (uklj. Related Work) → `02-metodologija` → `03-eksperimentalni-postav` → `04-rezultati` → `05-rasprava` → `06-zakljucak` |
| **Min. 5 znanstvenih radova**, svi **≥ 2021**, IEEE/Springer/Elsevier/ACM | 13 PDF-ova u [`data/sources/`](data/sources/); venue, godina, DOI i status za svaki u [`data/SOURCES_LOG.md`](data/SOURCES_LOG.md); BibTeX u [`docs/references.bib`](docs/references.bib) |
| Literatura **korištena**, ne samo citirana (odabir metode **i** usporedba) | Odabir metode: `docs/chapters/02-metodologija.tex` · Usporedba s vlastitim rješenjem: `docs/chapters/05-rasprava.tex` · Pregled po radu: [`TASK/LITERATURE.md`](TASK/LITERATURE.md) |
| **Implementacija** | [`src/`](src/) — cjeloviti cjevovod (≈ 7 800 redaka); 80 automatskih testova (`pytest src/tests -q`) |
| **Evaluacija** | 21 fizički pokus na UR3e: [`run_log.csv`](data/raw/lab_session_01092026_020000/telemetry/run_log.csv), 8 tablica u [`docs/tables/`](docs/tables/), grafovi u [`docs/figures/`](docs/figures/) |
| **Kod, konfiguracija i koraci za postavljanje** dokumentirani | [`src/README.md`](src/README.md), sva konfiguracija u `src/config/default.yaml`, protokoli u [`testing/lab/protocols/`](testing/lab/protocols/) |
| Fokus na **interakciju čovjek–robot** (pHRI) | `docs/chapters/05-rasprava.tex` + popunjena evaluacija u [`testing/lab/protocols/10_subjective_evaluation.md`](testing/lab/protocols/10_subjective_evaluation.md) |
| **Demonstracija praktičnog dijela** | Snimke svih 21 pokusa ([`camera/`](data/processed/video_clips_01092026/camera/)) i runbook za živu demonstraciju [`testing/lab/protocols/07_demo_runbook.md`](testing/lab/protocols/07_demo_runbook.md) |

---

## 3. Što sustav radi

Cjeloviti cjevovod za teleoperaciju kobota UR3e u realnom vremenu (125 Hz) pomoću
optičkog sustava OptiTrack. Podržana su dva načina rada:

- **1-DOF:** kut fleksije lakta operatera preslikan na zglob **J3** robota (lakat).
- **6-DOF:** tri kruta tijela (nadlaktica, podlaktica, šaka) preslikana na svih šest zglobova (J1–J6).
- **Sigurnosni lanac (4 sloja):** zasićenje brzine, ograničenje raspona, fail-safe pri
  okluziji markera (do 150 ms) i zaustavljanje u nuždi (E-stop).
- **Ispitano:** 21 fizički pokus na UR3e u laboratoriju + simulacijsko okruženje u VMware URSim-u.

```
[ OptiTrack Motive 3.0.1 ]
       │  (120 Hz, 3 kruta tijela / 11 markera)
       ▼  NatNet UDP (port 51000)
[ Upravljački cjevovod (Python 3.10) ] ── 125 Hz
  ├─ Prijemnik (UDP međuspremnik)
  ├─ Kinematika (3D poze -> kutovi zglobova)
  ├─ One-Euro adaptivni filtar (prigušenje šuma i tremora)
  └─ Četverostruka sigurnosna zaštita:
       • Zasićenje brzine (Rate Limiter)
       • Ograničenje radnog raspona (Range Clamp)
       • Fail-safe pri okluziji markera (Hold-last-state)
       • Zaustavljanje u nuždi (E-stop)
       │  RTDE servoJ naredbe (125 Hz, port 30004)
       ▼
[ Universal Robots UR3e ] (ili URSim u virtualnom okruženju)
```

---

## 4. Mapa repozitorija

Svaki direktorij ima vlastiti README s detaljima — ovdje je samo pregled što je gdje.

```
hri-seminar/
├── dist/          → GOTOV RAD: v1/HRI_seminar_Kresimir_Hartl.pdf (12 str.)
├── docs/          → LaTeX izvor rada, prezentacija, slike, tablice, analize
├── src/           → Izvorni kod cjevovoda (Python 3.10) + 80 testova
├── testing/       → Skripte i protokoli za laboratorij (lab/) i simulaciju (virtual/)
├── data/          → Svi eksperimentalni podaci, videozapisi i literatura
├── scripts/       → Kompilacija LaTeX dokumenta (build-docs.ps1 / .sh)
└── TASK/          → Tekst zadatka kolegija i pregled literature
```

| Direktorij | Sadrži | Vlastiti README |
|---|---|---|
| [`dist/`](dist/) | `v1/HRI_seminar_Kresimir_Hartl.pdf` — **predani rad**, jedina verzija | — |
| [`docs/`](docs/) | `main.tex` + `chapters/` (7 poglavlja), `references.bib`, `figures/` (15 datoteka), `tables/` (8 tablica generiranih iz telemetrije), `presentation/` | [`docs/README.md`](docs/README.md) |
| [`src/`](src/) | `optitrack/` (NatNet klijent i izvori), `kinematics/`, `filtering/` (One-Euro, Butterworth, EMA), `safety/`, `robot/` (RTDE), `pipeline/` (petlja 125 Hz), `tools/` (18 alata za analizu), `tests/` | [`src/README.md`](src/README.md) |
| [`testing/`](testing/) | `lab/` — protokoli sesije, izvršne skripte, dijagnostika, obrasci · `virtual/` — URSim skripte | [`testing/README.md`](testing/README.md), [`lab/`](testing/lab/README.md), [`virtual/`](testing/virtual/README.md) |
| [`data/`](data/) | `raw/` (Motive snimke, telemetrija 125 Hz, fotografije), `processed/` (izrezani videozapisi, benchmarki, sweepovi, usporedba sa simulacijom), `sources/` (literatura) | [`data/README.md`](data/README.md) |
| [`scripts/`](scripts/) | `build-docs.ps1`, `build-docs.sh` — kompilacija rada uz provjeru limita od 12 stranica | — |
| [`TASK/`](TASK/) | `TASK.md` (radni vodič), `original_task.md` (izvorni tekst zadatka), `LITERATURE.md`, `LABOS_CHECKLIST.md` | — |

---

## 5. Kako čitati oznake pokusa

Dvije oznake označavaju **isti** pokus, ovisno o tome gdje se gleda:

| Oznaka | Gdje se koristi | Primjer |
|---|---|---|
| **`T1a` … `T5e`** (javna) | rad, prezentacija, imena videozapisa | `T2a_filter_one_euro.mp4` |
| **`T-02` … `T-20`** (interna) | telemetrija, `run_log.csv`, protokoli sesije | `T-04` |

Potpuna tablica preslikavanja (javni ID ↔ interni ID ↔ videozapis) nalazi se u
**[`data/raw/lab_session_01092026_020000/telemetry/media_catalog.md`](data/raw/lab_session_01092026_020000/telemetry/media_catalog.md)**
— npr. `T2a` = `T-04` = pokus s One-Euro filtrom.

**Numeriranje zglobova:** rad i `.track.csv` datoteke koriste **1-bazirano** numeriranje
(J1–J6, lakat = **J3**), dok je CLI parametar `--joint` **0-baziran** (lakat = `--joint 2`).

---

## 6. Pokretanje (nije potrebno za pregled rada)

### 6.1 Priprema okruženja
```powershell
py -3.10 -m venv .venv           # Python 3.10 jer ur_rtde ima cp310 wheel
.\.venv\Scripts\Activate.ps1     # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 6.2 Testovi
```powershell
.venv\Scripts\python -m pytest src/tests -q     # očekivano: 80 passed
```

### 6.3 Kompilacija rada
```powershell
.\scripts\build-docs.ps1         # Windows
./scripts/build-docs.sh          # Linux / macOS
```
Rezultat: `dist/v1/HRI_seminar_Kresimir_Hartl.pdf`. Build ispisuje `Stranice: N / 12`;
ako N prijeđe 12, build se smatra neuspjelim. Detalji: [`docs/README.md`](docs/README.md).

### 6.4 Sustav bez robota (dry-run)
```powershell
.venv\Scripts\python -m src.pipeline.main --sink dry_run --seconds 20 --track-csv run.track.csv --log-actual
.venv\Scripts\python -m src.tools.track_analysis run.track.csv
```

Pokretanje na stvarnom robotu i sa živim OptiTrack streamom opisano je u
[`src/README.md`](src/README.md) i [`testing/lab/README.md`](testing/lab/README.md).

---

## 7. Pregled provedenih pokusa (21 fizički run na UR3e)

Preslikavanje na interne oznake i snimke Motive zaslona: [`media_catalog.md`](data/raw/lab_session_01092026_020000/telemetry/media_catalog.md).
Izmjerene vrijednosti po runu (latencija, jitter, RMSE, gubitak paketa): [`run_log.csv`](data/raw/lab_session_01092026_020000/telemetry/run_log.csv).

| Oznaka | Interni ID | Tip pokusa | Opis i parametri | Trajanje | Video (kamera) |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **T1a** | T-02 | Vjernost praćenja | 6-DOF prirodni tempo pokreta cijele ruke | 45 s | [`T1a_natural_tempo.mp4`](data/processed/video_clips_01092026/camera/T1a_natural_tempo.mp4) |
| **T1b** | T-03 | Prolaz po zglobovima | 6-DOF izolirano kretanje zglob-po-zglob | 45 s | [`T1b_joint_walkthrough.mp4`](data/processed/video_clips_01092026/camera/T1b_joint_walkthrough.mp4) |
| **T2a** | T-04 | Usporedba filtara | One-Euro filtar (fc = 1.0 Hz, beta = 0.005) | 30 s | [`T2a_filter_one_euro.mp4`](data/processed/video_clips_01092026/camera/T2a_filter_one_euro.mp4) |
| **T2b** | T-05 | Usporedba filtara | Bez filtriranja (sirovi mocap signal) | 30 s | [`T2b_filter_none.mp4`](data/processed/video_clips_01092026/camera/T2b_filter_none.mp4) |
| **T2c** | T-06 | Usporedba filtara | Butterworth filtar 2. reda (fc = 4.0 Hz) | 30 s | [`T2c_filter_butterworth.mp4`](data/processed/video_clips_01092026/camera/T2c_filter_butterworth.mp4) |
| **T2d** | T-07 | Usporedba filtara | Eksponencijalni prosjek (EMA, alpha = 0.2) | 33 s | [`T2d_filter_ema.mp4`](data/processed/video_clips_01092026/camera/T2d_filter_ema.mp4) |
| **T3a** | T-08 | Sigurnosni sloj | Zasićenje brzine (maks. 25 deg/s) | 25 s | [`T3a_rate_limit.mp4`](data/processed/video_clips_01092026/camera/T3a_rate_limit.mp4) |
| **T3b** | T-09 | Sigurnosni sloj | Ograničenje radnog raspona (+- 25 deg) | 25 s | [`T3b_range_limit.mp4`](data/processed/video_clips_01092026/camera/T3b_range_limit.mp4) |
| **T3c** | T-10 | Sigurnosni sloj | Okluzija markera nadlaktice (5.0 s prekid) | 30 s | [`T3c_marker_occlusion.mp4`](data/processed/video_clips_01092026/camera/T3c_marker_occlusion.mp4) |
| **T3d** | T-12a | Sigurnosni sloj | Zaustavljanje u nuždi (E-stop u 10 s + pendant) | 20 s | [`T3d_estop.mp4`](data/processed/video_clips_01092026/camera/T3d_estop.mp4) |
| **T6**  | T-20 | Dinamički odziv | 5 naglih trzaja rukom operatera | 30 s | [`T6_step_response.mp4`](data/processed/video_clips_01092026/camera/T6_step_response.mp4) |
| **T4a** | T-13a | Kašnjenje mreže | Dodano kašnjenje 0 ms (baza 385 ms) | 30 s | [`T4a_latency_0ms.mp4`](data/processed/video_clips_01092026/camera/T4a_latency_0ms.mp4) |
| **T4b** | T-13b | Kašnjenje mreže | Dodano kašnjenje 50 ms (ukupno 435 ms) | 30 s | [`T4b_latency_50ms.mp4`](data/processed/video_clips_01092026/camera/T4b_latency_50ms.mp4) |
| **T4c** | T-13c | Kašnjenje mreže | Dodano kašnjenje 100 ms (ukupno 485 ms) | 30 s | [`T4c_latency_100ms.mp4`](data/processed/video_clips_01092026/camera/T4c_latency_100ms.mp4) |
| **T4d** | T-13d | Kašnjenje mreže | Dodano kašnjenje 200 ms (move-and-wait) | 30 s | [`T4d_latency_200ms.mp4`](data/processed/video_clips_01092026/camera/T4d_latency_200ms.mp4) |
| **T4e** | T-13e | Kašnjenje mreže | Dodano kašnjenje 400 ms (ukupno 785 ms) | 30 s | [`T4e_latency_400ms.mp4`](data/processed/video_clips_01092026/camera/T4e_latency_400ms.mp4) |
| **T5a** | T-14 | Gubitak paketa | Stopa gubitka 0% (referentna baza) | 25 s | [`T5a_packet_loss_0pct.mp4`](data/processed/video_clips_01092026/camera/T5a_packet_loss_0pct.mp4) |
| **T5b** | T-15 | Gubitak paketa | Stopa gubitka 5% | 25 s | [`T5b_packet_loss_5pct.mp4`](data/processed/video_clips_01092026/camera/T5b_packet_loss_5pct.mp4) |
| **T5c** | T-16 | Gubitak paketa | Stopa gubitka 10% | 25 s | [`T5c_packet_loss_10pct.mp4`](data/processed/video_clips_01092026/camera/T5c_packet_loss_10pct.mp4) |
| **T5d** | T-17 | Gubitak paketa | Stopa gubitka 20% | 25 s | [`T5d_packet_loss_20pct.mp4`](data/processed/video_clips_01092026/camera/T5d_packet_loss_20pct.mp4) |
| **T5e** | T-18 | Gubitak paketa | Stopa gubitka 30% | 25 s | [`T5e_packet_loss_30pct.mp4`](data/processed/video_clips_01092026/camera/T5e_packet_loss_30pct.mp4) |

> Snimka Motive 3D prikaza postoji za 20 od 21 pokusa (za `T4c` nije zabilježena);
> nalazi se pod istim imenom u [`optitrack_screen/`](data/processed/video_clips_01092026/optitrack_screen/).

---

## 8. Licenca

Apache License 2.0 — [`LICENSE`](LICENSE)
