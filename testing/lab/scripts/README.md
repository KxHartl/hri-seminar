# scripts/ — izvršne skripte za rad u laboratoriju

Svaka skripta sama pokreće **most** prema Motiveu (`src.tools.live_sender`) i **cjevovod**,
i sama ih gasi — nije potreban drugi terminal. Pokreću se iz ovog direktorija u PowerShellu:

```powershell
cd testing\lab\scripts
.\00_check.ps1
```

Zadane adrese: robot `192.168.40.50`, Motive `192.168.40.31`, ovo računalo `192.168.40.30`.
Svaka se mijenja parametrom, npr. `.\02_free_motion.ps1 -RobotIp 192.168.40.51`.

## Pregled skripti

| Skripta | Robot se giba? | Što radi |
|---|:---:|---|
| `00_check.ps1` | ne | Preflight (paketi, SDK, config), RTDE stanje, odstupanje od referentne poze, provjera Motive streama |
| `01_home.ps1` | **da** (moveJ) | Vraća robota u referentnu pozu; `-Capture` sprema trenutnu kao novu, `-Show` samo ispiše odstupanje |
| `02_free_motion.ps1` | **da** | **6-DOF zadano** (svih 6 zglobova); 1-DOF uz `-Joint <N>` (0-bazirano, lakat = `-Joint 2` → J3) |
| `03_joint_walkthrough.ps1` | **da** | Vodi kroz zglobove jedan po jedan, s uputama i pauzama; mjeri svaki zglob zasebno |
| `04_axis_calibration.ps1` | ne | `arm_inspect` — popunjavanje `arm_axes` u configu prije 6-DOF rada |
| `05_free_6dof.ps1` | **da** | Cijela ruka → svih 6 zglobova, konzervativnije početne granice (±25°, 20 °/s) |
| `run_all_tests.ps1` | **da** | **Cijela ispitna matrica (T-02…T-20)** — vodi kroz sve testove i automatski sprema podatke |
| `_common.ps1` | — | Zajedničke funkcije (ne pokreće se izravno; učitavaju je ostale skripte) |

## Redoslijed prvi put u danu

```
00_check.ps1 → 01_home.ps1 → 04_axis_calibration.ps1 → 02_free_motion.ps1
                                                       (ili 03_joint_walkthrough.ps1)
```

## Najvažniji parametri

| Parametar | Skripte | Značenje |
|---|---|---|
| `-RobotIp`, `-MotiveIp`, `-ClientIp` | sve | Mrežne adrese (zadano `.50` / `.31` / `.30`) |
| `-Seconds` | `02`, `03`, `05` | Trajanje; `0` = kontinuirano do `Ctrl-C` |
| `-RangeDps` | `02`, `03`, `05` | Dopušteni ± otklon po zglobu [°] |
| `-SpeedDps` | `02`, `03`, `05` | Gornja granica brzine zgloba [°/s] |
| `-Joint <0..5>` | `02` | 1-DOF način; `-1` (zadano) = svih 6 zglobova |
| `-Joints "0,1,2"` | `03` | Koje zglobove proći, 0-bazirano |
| `-Sink dry_run` | `03` | Odvrti cijeli postupak **bez gibanja robota** |
| `-NoHome` | `02`, `05` | Preskoči povratak u referentnu pozu |
| `-Capture` / `-Show` | `01` | Spremi trenutnu pozu kao referentnu / samo ispiši odstupanje |

## Referentna poza („home")

Nije robotski home nego poza koja odgovara **ravnoj ispruženoj ruci**:
`[250, -180, 0, 0, 90, 0]°`, zapisana u `src/config/default.yaml` → `robot.home_q_deg`.

Svaki run kreće odatle. Bez toga svaki sljedeći run počinje ondje gdje je prethodni stao,
pa se dopušteni pojas zgloba pomiče (izmjereno 2026-08-31: lakat 0° → 20° → 37°).
Ako se robot namjesti drugačije i to se želi zadržati: `.\01_home.ps1 -Capture`.

## Sigurnost

- Nitko u radnom prostoru robota; **e-stop u ruci**; prekid svake skripte: **Ctrl-C**.
- Skripte koje gibaju robota traže potvrdu (Enter) prije pokreta.
- Ostaje uključeno i kad su granice široke: **fail-safe na gubitak signala**
  (> 150 ms bez okvira → robot stane) i sigurnosne granice u PolyScopeu.
- `-RangeDps` / `-SpeedDps` su glavna ručica za uža ili šira ograničenja;
  `-Sink dry_run` (skripta `03`) odvrti sve **bez gibanja robota**.

## Gdje završavaju podaci

Skripte pišu u `testing/lab/results/` (stvara se pri prvom pokretanju, nije u gitu):

| Skripta | Izlaz |
|---|---|
| `02`, `05` | `testing/lab/results/free/<tag>_<datum>.{csv,track.csv,track.png,summary.json}` |
| `03` | `testing/lab/results/` — po zglobu `J*.track.csv` + figure |
| `run_all_tests.ps1` | `testing/lab/results/T-XX.{csv,track.csv,summary.json,track.png}` |

Podaci provedene sesije (1.–2. 9. 2026.) arhivirani su u
[`data/raw/lab_session_01092026_020000/telemetry/`](../../../data/raw/lab_session_01092026_020000/telemetry/).

Detaljna analiza bilo kojeg zapisa (iz korijena repozitorija):

```powershell
.venv\Scripts\python -m src.tools.track_analysis <put_do>.track.csv
```

## Povezani dokumenti

- Postavke Motivea (streaming, kruta tijela, ID-evi): [`../protocols/09_motive_setup.md`](../protocols/09_motive_setup.md)
- Puni protokol sesije: [`../protocols/08_session_plan.md`](../protocols/08_session_plan.md)
- Šalabahter za labos: [`../protocols/cheatsheet.md`](../protocols/cheatsheet.md)
