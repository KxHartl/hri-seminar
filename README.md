# Upravljanje zglobom Universal Robots robota pomoću OptiTrack sustava u realnom vremenu

**Autor:** Krešimir Hartl ([kh239762@fsb.hr](mailto:kh239762@fsb.hr))  
**Rad (PDF):** [`dist/main.pdf`](dist/main.pdf) (ili [`dist/v1.5/main.pdf`](dist/v1.5/main.pdf), 12 str.)

---

## Pregled sustava

Ovaj repozitorij sadrži cjeloviti cjevovod za teleoperaciju kolaborativnog robota Universal Robots (UR3e) u realnom vremenu (125 Hz) pomoću optičkog sustava OptiTrack. Podržani su:
- **1-DOF način:** Praćenje kuta fleksije lakta preslikano na zglob J3 robota.
- **6-DOF način:** Istovremeno preslikavanje orijentacije i pozicije triju krutih tijela (nadlaktica, podlaktica, šaka) na svih šest zglobova robota (J1–J6).
- **Sigurnosni lanac:** Zasićenje brzine (rate limiter), ograničenje raspona (range clamp), fail-safe zadržavanje stanja pri okluziji markera (do 150 ms) te zaustavljanje u nuždi (E-stop).
- **Ispitivanje:** 21 fizikalni pokus na robotu UR3e u laboratoriju i simulacijsko okruženje u VMware URSim-u.

---

## Arhitektura toka podataka

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

## Struktura repozitorija

```
├── data/       # Eksperimentalni podaci (raw snimke, processed isječci i teleometrija)
├── dist/       # Kompajlirani PDF rada (dist/main.pdf i dist/v1.5/main.pdf)
├── docs/       # Izvorni LaTeX kod seminara, slike i tablice
├── scripts/    # Pomoćne skripte za kompilaciju LaTeX dokumenta
├── src/        # Programski paket teleoperacijskog cjevovoda (Python 3.10)
├── testing/    # Laboratorijske (lab/) i simulacijske (virtual/) testne skripte
└── TASK/       # Zadatak i specifikacija kolegija
```

- **`src/`**: Izvorni kod (kinematika, filtri, sigurnosni moduli, RTDE komunikacija, alati za analizu i 80 testova).
- **`testing/`**:
  - `testing/lab/`: Izvršne skripte (`run_all_tests.ps1`, `00_check.ps1`, itd.), protokoli pokusa i dijagnostika.
  - `testing/virtual/`: Skripte za izvođenje i verifikaciju unutar VMware URSim simulatora.
- **`data/`**:
  - `data/raw/`: Sirovi podaci sa sesije (Motive `.tak` datoteke, master `.mkv` snimke zaslona, fotografije postava, 125 Hz teleometrija).
  - `data/processed/`: Isječeni pojedinačni videozapisi pokusa (`video_clips_01092026/`), benchmark filtara, sweeps gubitka paketa.
  - `data/sources/`: 13 recenziranih znanstvenih radova.

---

## Upute za pokretanje

### 1. Priprema okruženja
```bash
# Kreiranje virtualnog okruženja (Python 3.10)
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1    # Linux: source .venv/bin/activate

# Instalacija paketa
pip install -r requirements.txt
```

### 2. Pokretanje testnog skupa
```bash
# Provjera testova
pytest src/tests -q
```

### 3. Kompilacija LaTeX rada
```powershell
# Windows PowerShell
.\scripts\build-docs.ps1

# Linux / macOS (Bash)
./scripts/build-docs.sh
```
Generirani dokument sprema se u `dist/main.pdf` i `dist/v1.5/main.pdf` (točno 12 stranica).

### 4. Pokretanje simulacije (dry-run)
```bash
# Test teleoperacije u simulaciji bez robota (20 sekundi)
python -m src.pipeline.main --sink dry_run --seconds 20 --track-csv run.track.csv --log-actual

# Analiza performansi snimljenog traga
python -m src.tools.track_analysis run.track.csv
```

---

## Pregled provedenih pokusa (21 fizikalni run na UR3e)

| Oznaka | Tip pokusa | Opis i parametri | Trajanje | Kamera video |
| :---: | :--- | :--- | :---: | :--- |
| **T1a** | Vjernost praćenja | 6-DOF prirodni tempo pokreta cijele ruke | 45 s | [`T1a_natural_tempo.mp4`](data/processed/video_clips_01092026/camera/T1a_natural_tempo.mp4) |
| **T1b** | Prolaz po zglobovima | 6-DOF izolirano kretanje zglob-po-zglob | 45 s | [`T1b_joint_walkthrough.mp4`](data/processed/video_clips_01092026/camera/T1b_joint_walkthrough.mp4) |
| **T2a** | Usporedba filtara | One-Euro filtar (fc = 1.0 Hz, beta = 0.005) | 30 s | [`T2a_filter_one_euro.mp4`](data/processed/video_clips_01092026/camera/T2a_filter_one_euro.mp4) |
| **T2b** | Usporedba filtara | Bez filtriranja (sirovi mocap signal) | 30 s | [`T2b_filter_none.mp4`](data/processed/video_clips_01092026/camera/T2b_filter_none.mp4) |
| **T2c** | Usporedba filtara | Butterworth filtar 2. reda (fc = 4.0 Hz) | 30 s | [`T2c_filter_butterworth.mp4`](data/processed/video_clips_01092026/camera/T2c_filter_butterworth.mp4) |
| **T2d** | Usporedba filtara | Eksponencijalni prosjek (EMA, alpha = 0.2) | 33 s | [`T2d_filter_ema.mp4`](data/processed/video_clips_01092026/camera/T2d_filter_ema.mp4) |
| **T3a** | Sigurnosni sloj | Zasićenje brzine (maks. 25 deg/s) | 25 s | [`T3a_rate_limit.mp4`](data/processed/video_clips_01092026/camera/T3a_rate_limit.mp4) |
| **T3b** | Sigurnosni sloj | Ograničenje radnog raspona (+- 25 deg) | 25 s | [`T3b_range_limit.mp4`](data/processed/video_clips_01092026/camera/T3b_range_limit.mp4) |
| **T3c** | Sigurnosni sloj | Okluzija markera nadlaktice (5.0 s prekid) | 30 s | [`T3c_marker_occlusion.mp4`](data/processed/video_clips_01092026/camera/T3c_marker_occlusion.mp4) |
| **T3d** | Sigurnosni sloj | Zaustavljanje u nuždi (E-stop u 10 s + pendant) | 20 s | [`T3d_estop.mp4`](data/processed/video_clips_01092026/camera/T3d_estop.mp4) |
| **T6**  | Dinamički odziv | 5 naglih trzaja rukom operatera | 30 s | [`T6_step_response.mp4`](data/processed/video_clips_01092026/camera/T6_step_response.mp4) |
| **T4a** | Kašnjenje mreže | Dodano kašnjenje 0 ms (baza 385 ms) | 30 s | [`T4a_latency_0ms.mp4`](data/processed/video_clips_01092026/camera/T4a_latency_0ms.mp4) |
| **T4b** | Kašnjenje mreže | Dodano kašnjenje 50 ms (ukupno 435 ms) | 30 s | [`T4b_latency_50ms.mp4`](data/processed/video_clips_01092026/camera/T4b_latency_50ms.mp4) |
| **T4c** | Kašnjenje mreže | Dodano kašnjenje 100 ms (ukupno 485 ms) | 30 s | [`T4c_latency_100ms.mp4`](data/processed/video_clips_01092026/camera/T4c_latency_100ms.mp4) |
| **T4d** | Kašnjenje mreže | Dodano kašnjenje 200 ms (move-and-wait) | 30 s | [`T4d_latency_200ms.mp4`](data/processed/video_clips_01092026/camera/T4d_latency_200ms.mp4) |
| **T4e** | Kašnjenje mreže | Dodano kašnjenje 400 ms (ukupno 785 ms) | 30 s | [`T4e_latency_400ms.mp4`](data/processed/video_clips_01092026/camera/T4e_latency_400ms.mp4) |
| **T5a** | Gubitak paketa | Stopa gubitka 0% (referentna baza) | 25 s | [`T5a_packet_loss_0pct.mp4`](data/processed/video_clips_01092026/camera/T5a_packet_loss_0pct.mp4) |
| **T5b** | Gubitak paketa | Stopa gubitka 5% | 25 s | [`T5b_packet_loss_5pct.mp4`](data/processed/video_clips_01092026/camera/T5b_packet_loss_5pct.mp4) |
| **T5c** | Gubitak paketa | Stopa gubitka 10% | 25 s | [`T5c_packet_loss_10pct.mp4`](data/processed/video_clips_01092026/camera/T5c_packet_loss_10pct.mp4) |
| **T5d** | Gubitak paketa | Stopa gubitka 20% | 25 s | [`T5d_packet_loss_20pct.mp4`](data/processed/video_clips_01092026/camera/T5d_packet_loss_20pct.mp4) |
| **T5e** | Gubitak paketa | Stopa gubitka 30% | 25 s | [`T5e_packet_loss_30pct.mp4`](data/processed/video_clips_01092026/camera/T5e_packet_loss_30pct.mp4) |

Cjeloviti registar parametara i teleometrije dostupan je u [`data/raw/lab_session_01092026_020000/telemetry/run_log.csv`](data/raw/lab_session_01092026_020000/telemetry/run_log.csv).
