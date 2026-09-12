# Real-time OptiTrack → UR teleoperacijski cjevovod (`src/`)

Upravljanje zglobovima cobota Universal Robots (UR3e / URSim) iz pokreta ljudske ruke praćene
OptiTrack sustavom u realnom vremenu (125 Hz). Podržana su dva načina rada:
1. **1-DOF izolirani lakat (`segment`):** Kut fleksije lakta iz triju ishodišta segmenata mapiran na **J3 (lakat)**.
2. **6-DOF puna ruka (`multi_joint`):** Tri kruta tijela (nadlaktica, podlaktica, šaka) mapiraju se u realnom vremenu na svih 6 zglobova robota (**J1–J6**).

Arhitektura je izvor/odredište agnostična: isti cjevovod radi u simulaciji (URSim), izvanmrežno (replay) i na stvarnom fizičkom robotu UR3e.

## Arhitektura

```
OptiTrack Motive ─► NatNet UDP ─► receiver ─► kinematičko ─► One-Euro ─► 4-stupanjski ─► RTDE servoJ ─► UR3e
  (3 kruta tijela,    (port 51000,    (buffer,   preslikavanje   filtar     sigurnosni     (125 Hz,       (stvarno
   120 Hz mocap)       loss/jitter)    pacing)    (3D poze→kutovi)          štit           port 30004)    gibanje)
                                                                           │
                                            ┌──────────────────────────────┴──────────────────────────────┐
                                            │ 1. Rate Limiter (maks. brzina °/s)                          │
                                            │ 2. Range Clamp (radni prostor min/max)                      │
                                            │ 3. Marker Occlusion Fail-Safe (zadržavanje stanja do 150 ms)│
                                            │ 4. Emergency Stop (softversko zamrzavanje + teach pendant)  │
                                            └─────────────────────────────────────────────────────────────┘
```

Moduli: `optitrack/` (NatNet klijent, mock/live izvori, CSV loader), `receiver.py`,
`kinematics/` (preslikavanje 3 rigid-bodyja `ArmPoseMapper`, kut lakta `SegmentAngleMapper`),
`filtering/` (One-Euro, Butterworth, EMA, tvornica filtara), `safety/guard.py` (četverostruka zaštita),
`robot/` (RTDE backend, dry-run), `pipeline/` (glavna petlja na 125 Hz, mjerenje latencije),
te `tools/` (analiza teleometrije, generator slika, agregacija rezultata).

## Postavljanje

```bash
# Python 3.10 (ur_rtde ima cp310 wheel; novije verzije možda nemaju)
py -3.10 -m venv .venv
.venv/Scripts/python -m pip install -r src/requirements.txt
```

Konfiguracija: `src/config/default.yaml` (izvor, odredište, IP, zglob, filtri, sigurnosne
granice, control_hz). Mijenjaj parametre ondje — nikad hardkodirano u kodu.

## Pokretanje

```bash
# 0) Provjera RTDE veze + mali servoJ sweep na J4 (URSim mora biti u Remote Control modu)
.venv/Scripts/python -m src.tools.check_ursim --ip 192.168.208.128

# 1) Cijeli pipeline (replay → URSim), 20 s
.venv/Scripts/python -m src.pipeline.main --config src/config/default.yaml --seconds 20

# 1b) Bez robota (offline test cijelog puta)
.venv/Scripts/python -m src.pipeline.main --sink dry_run --seconds 5

# 2) Vjeran 120 Hz replay (zaseban proces — kao stvarni Motive); u drugom terminalu
#    pokreni pipeline s istim udp portom (npr. 51000) i source.kind nepromijenjen.
.venv/Scripts/python -m src.tools.replay_sender --port 51000

# 3) Benchmark filtara i osjetljivosti (→ data/processed/, uklj. filter_bench.summary.json)
.venv/Scripts/python -m src.tools.benchmark
.venv/Scripts/python -m src.tools.benchmark --track data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv --joint 3

# 4) Spremnost prije lab sesije (venv, NatNet SDK, config, dokumenti)
.venv/Scripts/python -m src.tools.preflight

# Testovi
.venv/Scripts/python -m pytest src/tests -q
```

### Logiranje kutova (vjernost praćenja)

Latencijski log bilježi samo vrijeme; da bi se mjerilo **koliko vjerno** robot prati ruku,
uključi i log kutova:

```bash
.venv/Scripts/python -m src.pipeline.main --sink dry_run --seconds 20   --track-csv run.track.csv --log-actual
.venv/Scripts/python -m src.tools.track_analysis run.track.csv     # RMSE, lag, overlay figura
```

`run.track.csv` po taktu i po zglobu sadrži ulazni (sirovi) kut, filtrirani, target prije
sigurnosnog sloja, naredbu i — uz `--log-actual` — **stvarni** kut robota, plus zastavice
`ratelim/rangeclamp/halted`. Kolone su **1-bazirane (J1–J6)** kao u radu, dok je `--joint`
0-baziran (lakat = `--joint 2` = J3).

| Flag | Namjena |
|---|---|
| `--track-csv PUT` | uključi log kutova (bez njega se kutovi ne bilježe) |
| `--log-actual` | čitaj i stvarni kut robota (RTDE `getActualQ`) |
| `--track-decimate N` | zapiši svaki N-ti takt (dugi runovi; smanjuje i cijenu RTDE čitanja) |
| `--added-latency-ms N` | umjetno kašnjenje prije sigurnosnog sloja (mjerenje utjecaja latencije) |
| `--signal-timeout-s S` | mora biti **iznad** dodane latencije, inače fail-safe drži trajno |
| `--estop-after S` | okini softverski e-stop nakon S sekundi (dokazni test) |
| `--gain G`, `--invert` | razmjer/smjer preslikavanja bez diranja `default.yaml` |

## Prelazak na stvarni robot (UR3e) i živi OptiTrack

Živi izvor je implementiran: most `src.tools.live_sender` čita Motive preko NatNet SDK-a
(`--sdk` = kut lakta, `--arm` = 6 kanala cijele ruke) i šalje našim UDP formatom, pa
pipeline ostaje nepromijenjen (`--external --port 51000`).

1. Most u jednom terminalu, pipeline u drugom (**točno jedan** most po portu).
2. Odredište: `--sink ur3e --ip 192.168.40.50`. Lab robot je od 2026-08-31 **UR3e**
   (PolyScope 5.9.5), pa **treba „Remote Control" mod** uz mode RUNNING. (Raniji
   robot je bio UR3/CB3 na `.27`, gdje taj mod ne postoji.)
3. Kreni s konzervativnim granicama (`--max-speed-dps 12–15`, `--range-dps 15–20`) i
   otpuštaj postupno; e-stop na dohvat ruke.

Protokol sesije i točne komande: `testing/lab/protocols/08_session_plan.md` i `testing/lab/protocols/cheatsheet.md`.

Detalji parametara i opravdanja: `TASK/LITERATURE.md`, `TASK/TASK.md`; format podataka:
`data/raw/reference_mocap/README.md`.
