# run_scripts — skripte za labos (pokrećeš ih ti)

Svaka skripta sama pokreće **most** (`live_sender`) i **pipeline**, i sama ga gasi —
ne treba ti drugi terminal. Pokreni iz ovog foldera u PowerShellu:

```powershell
cd testing/lab\run_scripts
.\00_provjera.ps1
```

Zadane adrese: robot `192.168.40.50`, Motive `192.168.40.31`, PC `192.168.40.30`.
Svaka se mijenja parametrom, npr. `.\02_slobodno_gibanje.ps1 -RobotIp 192.168.40.51`.

| Skripta | Robot se giba? | Što radi |
|---|---|---|
| `00_provjera.ps1` | ne | preflight, RTDE stanje, odstupanje od referentne poze, Motive stream |
| `01_home.ps1` | **da** (moveJ) | vrati robota u referentnu pozu; `-Capture` sprema trenutnu kao novu, `-Show` samo ispiše |
| `02_slobodno_gibanje.ps1` | **da** | **6-DOF zadano** (svih 6 zglobova); ili 1-DOF uz `-Joint <N>` (npr. `-Joint 2` za lakat -> J3) |
| `03_hod_po_zglobovima.ps1` | **da** | vodi kroz zglobove jedan po jedan, s uputama i pauzama; mjeri svaki zglob posebno |
| `04_kalibracija_osi.ps1` | ne | `arm_inspect` — popunjavanje `arm_axes` prije 6-DOF |
| `05_slobodno_6dof.ps1` | **da** | cijela ruka → svih 6 zglobova (konzervativnije početne granice) |
| `pokreni_sve_testove.ps1` | **da** | **cijela ispitna matrica (T-02..T-18)** — vodi te kroz sve testove i automatski sve sprema |

## Redoslijed prvi put u danu

```
00_provjera.ps1 → 01_home.ps1 → 04_kalibracija_osi.ps1 → 02_slobodno_gibanje.ps1
                                                         (ili 03_hod_po_zglobovima.ps1)
```

## Referentna poza („home")

Nije robotski home nego poza koja odgovara **ravnoj ispruženoj ruci**:
`[250, -180, 0, 0, 90, 0]°`, u `src/config/default.yaml` → `robot.home_q_deg`.
Svaki run kreće odatle; bez toga svaki sljedeći run počinje ondje gdje je prethodni
stao pa se dopušteni pojas zgloba pomiče (izmjereno: lakat 0° → 20° → 37°).
Ako robota namjestiš drugačije i želiš to zadržati: `.\01_home.ps1 -Capture`.

## Sigurnost

- Nitko u radnom prostoru robota; **e-stop u ruci**; prekid svake skripte: **Ctrl-C**.
- Skripte koje gibaju robota traže potvrdu (Enter) prije pokreta.
- Ostaje uključeno i kad su granice široke: **fail-safe na gubitak signala**
  (>150 ms bez okvira → robot stane) i PolyScope sigurnosne granice.
- `-RangeDps` / `-SpeedDps` su jedina ručica za uža/šira ograničenja; `-Sink dry_run`
  (skripta 03) odvrti cijeli postupak **bez gibanja robota**.

## Gdje završe podaci

| Skripta | Izlaz |
|---|---|
| `02`, `05` | `data/raw/lab_session_01092026_020000/telemetry/exploratory/free/<tag>_<datum>.{csv,track.csv,track.png}` |
| `03` | `data/raw/lab_session_01092026_020000/telemetry/exploratory/walkthrough/J*.track.csv` (+ figure) |

Detaljna analiza bilo kojeg zapisa:

```powershell
..\..\.venv\Scripts\python -m src.tools.track_analysis <put_do>.track.csv
```

Postavke Motivea (streaming, kruta tijela, ID-evi): `../10_MOTIVE_SETUP.md`.
Puni protokol sesije: `../09_PLAN_SESIJE.md`.
