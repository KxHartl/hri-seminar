# 09 — PLAN SESIJE (novi odlazak): prikupljanje SVIH podataka

> Ovo je dokument koji nosiš u labos. Zamjenjuje matricu `P1-*/P2-*` iz
> `02_TEST_PROTOCOL.md` (pisana za UR3e + markere šake, nikad izvedena).
> Numeracija je sada **T-01…T-21**.

## Zašto ova sesija

Prošli put su snimljeni **samo vremenski podaci** — svi CSV-ovi u `results/` imaju
`t_capture, t_command, latency_ms, signal_age_ms` i **nijedan kut**. Zato se središnja
tvrdnja rada (robot vjerno prati ruku) ne može ni izračunati unatrag, a sigurnosni
slojevi (rate-limit, range-clamp, fail-safe, e-stop) nisu nikad izmjereni na robotu.

Sada pipeline logira i kutove (`--track-csv`) i **stvarni kut robota** (`--log-actual`),
pa svaki run ispod daje brojku, ne dojam.

---

## Novi flagovi (razlika u odnosu na prošli put)

| Flag | Čemu služi |
|---|---|
| `--track-csv <put>` | CSV s kutovima po zglobu: `in_ / filt_ / target_ / cmd_ [/ act_]` + zastavice sigurnosti. **Bez ovog flaga kutovi se ne logiraju.** |
| `--log-actual` | uz `--track-csv`: čitaj i **stvarni** kut robota (RTDE `getActualQ`) |
| `--track-decimate N` | zapiši svaki N-ti takt (za endurance; 10 min bez decimacije = 20 MB) |
| `--added-latency-ms N` | umjetno kašnjenje ulaza (mjerenje utjecaja latencije) |
| `--signal-timeout-s S` | **obavezno podigni iznad dodane latencije**, inače fail-safe drži trajno |
| `--estop-after S` | okini softverski e-stop nakon S sekundi (dokazni test) |
| `--gain G` / `--invert` | ispravi razmjer/smjer bez diranja `default.yaml` |

Kolone su imenovane **1-bazirano (J1–J6)** kao u radu; `--joint` je i dalje
**0-baziran** (lakat = `--joint 2` = J3).

---

## Prije izlaska iz kuće

    .venv/Scripts/python -m src.tools.preflight
    .venv/Scripts/python -m pytest src/tests -q

Suha proba cijelog 6-DOF puta bez Motivea (dva terminala):

    .venv/Scripts/python -m src.tools.live_sender --mock-arm --port 51000
    .venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink dry_run --mode multi_joint --seconds 15 --track-csv x6.track.csv --log-actual

Preflight provjerava venv, **NatNet SDK** (nije vendoran u repo — pobrisani Downloads
tiho ruše živi izvor), config + kalibraciju `arm_axes`, put za logiranje kutova i
lab-dokumente. Izlazi s greškom ako nešto nedostaje. U labosu ga možeš pokrenuti i s
`--robot 192.168.40.50 --motive 192.168.40.31`.

---

## B0. Postavljanje (~45 min)

1. **Mreža** — samo JEDAN NIC na `192.168.40.0/24` (PC `.30`). S dva NIC-a Windows
   rutira na krivi kabel i robot `.27` izgleda nedostupno.

       ipconfig | findstr 192.168.40
       ping 192.168.40.50

2. **Robot** — power on, brake release, mode 7. Od 2026-08-31 je to **UR3e**, pa
   **treba** "Remote Control" mod (☰ → Settings → System → Remote Control → Enable,
   pa gornji desni prekidač → *Remote*); provjera: dashboard `is in remote control`.

       .venv/Scripts/python -m src.tools.check_ursim --ip 192.168.40.50 --no-move
       .venv/Scripts/python -m src.tools.check_ursim --ip 192.168.40.50

   (drugi red radi ±5° sweep — **prazan prostor!**)

3. **Motive** — unicast, Local Interface `192.168.40.31`, Stream Markers + Rigid Bodies ON.

       .venv/Scripts/python testing/lab/diag/sdk_inspect.py 192.168.40.31 192.168.40.30

   Potvrdi stream ID-eve: `nadlaktica`=25, `podlaktica`=24, `saka`=16 (od 2026-08-31;
   u lipnju su bili 18/17/16 — ID-evi se mijenjaju kad se tijela naprave iznova). **Ako su kruta
   tijela iznova definirana, ID-evi su drugi** → proslijedi ih mostu preko
   `--id-upper/--id-fore/--id-hand`.

4. **Rekalibracija osi** — preskoči SAMO ako su rigid bodyji isti kao 2026-06-27:

       .venv/Scripts/python testing/lab/diag/arm_inspect.py 192.168.40.31 192.168.40.30

   Home s **ispruženom rukom**, pa 6 izoliranih pokreta; provjeri da `arm_axes` u
   `src/config/default.yaml` još odgovara (seq / idx / predznak).

5. **Provjera takta uz `--log-actual`** (jedino što se nije dalo izmjeriti kod kuće:
   koliko RTDE `getActualQ()` košta unutar 8 ms takta pravog UR3). Dva kratka runa:

       .venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink ur3e --ip 192.168.40.50 --joint 2 --seconds 15 --range-dps 20 --max-speed-dps 15 --latency-csv data/raw/lab_session_01092026_020000/telemetry/chk-bez.csv
       .venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink ur3e --ip 192.168.40.50 --joint 2 --seconds 15 --range-dps 20 --max-speed-dps 15 --latency-csv data/raw/lab_session_01092026_020000/telemetry/chk-sa.csv --track-csv data/raw/lab_session_01092026_020000/telemetry/chk-sa.track.csv --log-actual

   Usporedi `median_ms` i `rx_rate_hz` iz oba summary JSON-a. Ako je razlika > ~1 ms ili
   frekvencija padne, dodaj `--track-decimate 5` u sve daljnje runove (to smanjuje i broj
   RTDE čitanja, ne samo redaka). *Na dry-run harnessu razlika je bila unutar šuma.*

6. **Potpiši `templates/safety_signoff.md`** prije prvog gibanja robota.

7. **FOTOGRAFIJA POSTAVA ODMAH** → `docs/figures/setup_photo.jpg`. Rad je pokupi
   automatski (sada je tamo prazan okvir). Kopija i širi kadar u `results/media/`.

> Most (`live_sender`) i pipeline **na istom računalu** — inače latencija nije valjana.
> Točno **jedan** most na portu 51000 (dva mosta = lažnih 240 Hz i 38 % "gubitka").

---

## B1. Motive snimke — PRVO, dok si svjež

Snimi 2 takea i exportaj CSV u `data/optitrack/live/`:

| Datoteka | Sadržaj |
|---|---|
| `elbow_slow_fast.csv` | 60 s: 20 s sporo, 20 s srednje, 20 s brzo savijanje lakta |
| `arm_6dof.csv` | 60 s prirodnog gibanja cijele ruke |

Osiguranje: ako robot kasnije zablokira, offline analize se ipak mogu ponoviti kod kuće.

---

## Standardni oblik komande

**Terminal A — most (drži upaljeno cijelu fazu):**

    # 1-DOF (kut lakta)
    .venv/Scripts/python -m src.tools.live_sender --sdk --server-ip 192.168.40.31 --client-ip 192.168.40.30 --port 51000

    # 6-DOF (cijela ruka)
    .venv/Scripts/python -m src.tools.live_sender --arm --server-ip 192.168.40.31 --client-ip 192.168.40.30 --id-upper 25 --id-fore 24 --id-hand 16 --port 51000

**Terminal B — pipeline (jedan po testu):**

    .venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink ur3e --ip 192.168.40.50 --joint 2 --seconds 60 --range-dps 30 --max-speed-dps 25 --latency-csv data/raw/lab_session_01092026_020000/telemetry/T-XX.csv --track-csv data/raw/lab_session_01092026_020000/telemetry/T-XX.track.csv --log-actual

Za 6-DOF dodaj `--mode multi_joint` i izostavi `--joint`.

---

## B2. Vjernost praćenja — NAJVAŽNIJE

| ID | Postav | Razlika u komandi | Trajanje |
|---|---|---|---|
| **T-01** | 1-DOF lakat→J3, URSim | `--sink ursim --ip <URSim IP>` | 60 s |
| **T-02** | 1-DOF lakat→J3, **UR3** | standardni oblik gore | 60 s |
| **T-03** | 6-DOF, **UR3** | `--mode multi_joint --range-dps 15 --max-speed-dps 12` | 60 s |

Pokret: **20 s sporo / 20 s srednje / 20 s brzo** — da se lag i RMSE vide u više režima.
Ako robot ide na krivu stranu → dodaj `--invert` (ne diraj config).

> T-02 ujedno ispravlja netočnost u radu: redak 1 tablice tvrdi "lakat → J3", a taj je
> run zapravo vozio wrist_2 (J5) reprodukcijom stare snimke šake.

**Provjeri odmah, dok se run još može ponoviti:**

    .venv/Scripts/python -m src.tools.track_analysis data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv

---

## B3. Filtri na stvarnom robotu

**T-04…T-07** — isti pokret ~30 s, mijenja se samo filtar:

| ID | Dodaj |
|---|---|
| T-04 | `--filter one_euro` |
| T-05 | `--filter none` |
| T-06 | `--filter butterworth` |
| T-07 | `--filter ema` |

Nakon svakog upiši u run-log kratku bilješku o glatkoći.

---

## B4. Sigurnost — E-STOP U RUCI, VIDEO OBAVEZAN

| ID | Test | Komanda / postupak | Što dokazuje |
|---|---|---|---|
| **T-08** | Rate-limit | `--max-speed-dps 15`, brzi flick lakta | `ratelim_J3` > 0, izmjerena maks. brzina naredbe |
| **T-09** | Range-limit | `--range-dps 20`, namjerno prekorači raspon | `rangeclamp_J3` > 0, robot stane na granici |
| **T-10** | Fail-safe (okluzija) | rukom prekrij markere ~3 s, pa vrati | `halted` takti, skok `signal_age_ms` |
| **T-11** | Fail-safe (prekid) | ugasi Terminal A usred runa | isto, čist prekid |
| **T-12a** | Softverski e-stop | `--estop-after 15 --seconds 30` | izlaz zamrznut, `halted` u track CSV-u |
| **T-12b** | Hardverski e-stop | pritisni gumb tijekom gibanja | video + bilješka o oporavku |

Videe spremi kao `data/raw/lab_session_01092026_020000/camera/T-xx_<opis>.mp4`.

---

## B5. Utjecaj kašnjenja (objektivno)

**T-13a…T-13e** — 1-DOF lakat→J3 na UR3, ~45 s po postavci, isti tempo pokreta:

| ID | Dodaj |
|---|---|
| T-13a | `--added-latency-ms 0   --signal-timeout-s 0.15` |
| T-13b | `--added-latency-ms 50  --signal-timeout-s 0.30` |
| T-13c | `--added-latency-ms 100 --signal-timeout-s 0.40` |
| T-13d | `--added-latency-ms 200 --signal-timeout-s 0.60` |
| T-13e | `--added-latency-ms 400 --signal-timeout-s 0.90` |

- Timeout MORA biti iznad dodane latencije: starost signala uključuje dodano
  kašnjenje, pa bi inače fail-safe držao trajno i run ne bi mjerio ništa.
- Pri 200–400 ms robot vidljivo kasni: uske granice, **ne ulaziš u radni prostor**.

Zapiši i vlastitu bilješku po postavci ("na ___ ms počinje smetati").

---

## B6. Kontrolirani gubitak paketa

**T-14…T-18** — isti pokret ~30 s: `--drop-rate 0 / 0.05 / 0.10 / 0.20 / 0.30`.
Provjeri da `rx_loss_pct` u summary JSON-u odgovara traženom postotku.

---

## B7. Endurance

**T-19** — 10 minuta, 6-DOF, uske granice:

    --mode multi_joint --seconds 600 --range-dps 15 --max-speed-dps 12 --track-decimate 5

Gibaj se povremeno, ne cijelo vrijeme. Cilj: bez drifta, bez teških repova latencije.

---

## B8. Nagli pokret

**T-20** — 5 brzih "flickova" lakta na UR3 (~30 s), standardni oblik.
Zamjenjuje sintetički step-odziv koji je sada u radu.

**T-21** (rezerva) — ponovi T-02 na kraju dana radi ponovljivosti.

---

## B9. Zatvaranje sesije (~20 min)

- [ ] Svi `data/raw/lab_session_01092026_020000/telemetry/T-*.csv`, `*.track.csv`, `*.summary.json` na disku
- [ ] `data/optitrack/live/*.csv` (Motive export)
- [ ] `docs/figures/setup_photo.jpg` + videi u `results/media/`
- [ ] Popunjen `templates/run_log.csv`, potpisan `templates/safety_signoff.md`
- [ ] Sanity provjera:

          .venv/Scripts/python -m src.tools.track_analysis data/raw/lab_session_01092026_020000/telemetry/T-02.track.csv
          .venv/Scripts/python -m src.tools.track_analysis data/raw/lab_session_01092026_020000/telemetry/T-03.track.csv

- [ ] `.\.ai\scripts\helpers\checkpoint.ps1 "data: 🤖 [AI] lab rezultati <datum>"`

## Ako dan skrati

Minimum: **B0 → B1 → T-02, T-03 → T-10, T-12 → T-13a/c/e → T-19.**
To pokriva vjernost, sigurnost, utjecaj kašnjenja i kontinuirani rad.

## Ako gori

Neočekivano gibanje → **E-STOP**. Sigurnost > podatak. Zatim `04_TROUBLESHOOTING.md`.
