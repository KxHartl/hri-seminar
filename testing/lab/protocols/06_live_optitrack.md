# 06 — ŽIVI OPTITRACK: status i handoff

Stanje na kraju **2026-06-26** i plan za sljedeći lab. Faza 2 (Motive → bridge →
pipeline → robot). Diagnostika: `testing/lab/diag/` (vidi README).

> ⚠️ **2026-08-31 — hardver se promijenio.** Robot u labosu više nije UR3/CB3 na
> `192.168.40.27`, nego **UR3e (PolyScope 5.9.5) na `192.168.40.50`**, koji **traži**
> „Remote Control" mod. Adrese i tvrdnje o CB3 niže su **povijesni zapis lipanjske
> sesije**; aktualne komande su u `CHEATSHEET.md` i `09_PLAN_SESIJE.md`.

## ✅ Riješeno danas

1. **Robot UR3/CB3** (`192.168.40.27`, PolyScope 3.12) — RTDE veza + kontrola potvrđena.
   - CB3 **nema "Remote Control" mod** (to je e-Series); RTDE radi direktno (mode 7).
   - Prvi pravi run: replay snimke → wrist_2, suženi safety; latencija median 4 ms, 0% gubitka
     (`data/raw/lab_session_01092026_020000/telemetry/P1-00-firstcontact.csv`).
   - Pipeline override flagovi dodani: `--ip --joint --range-dps --max-speed-dps`.
2. **Mreža** — robot + Motive + PC na **istom switchu** (`.27` / `.31` / `.30`).
3. **Motive streaming** radi: Local Interface `.31`, **Unicast**, 120 Hz.
   Multicast je davao **0 okvira** (switch/IGMP) → koristimo **unicast**.
4. **Živi transport potvrđen** s našim parserima: NatNet zahtijeva `NAT_CONNECT` +
   periodični `KEEPALIVE`, a u unicastu frameovi dolaze na **komandni socket**
   (~480 okvira/4 s). Mehanika izvučena iz NatNet SDK 4.5.

## ⚠️ Otvoreno / odluke

- **Model-def (imena markera)**: naš `src/optitrack/natnet` parser **ne čita NatNet 4.0**
  model-definicije (size-polje po datasetu tek od 4.1; dataseti u proizvoljnom redu).
  **Odluka**: imena/segmente vaditi preko **SDK klijenta**; živi izvor graditi na njemu.
  SDK: `NATNET_SDK` env → `...\NatNet_SDK_4.5_windows\NatNetSDK\Samples\PythonClient`.
- **Druga NIC** `Ethernet 4` (`.22`) na istoj podmreži — ostavljena; idealno ugasiti
  da ne muti rutiranje/multicast.
- **Vendoranje SDK-a**: 3 fajla (`NatNetClient.py`, `DataDescriptions.py`, `MoCapData.py`)
  zasad se učitavaju iz Downloads foldera. Razmotriti kopiranje u repo (uz napomenu o
  porijeklu/EULA) radi reproducibilnosti.

## 🔜 SUTRA — plan

### A. Definicija markera/segmenata u Motiveu
Korisnik radi: **markeri + koordinatne osi po segmentima** — `zapesce`, `podlaktica`,
`nadlaktica`. ⚠️ **Promjena smjera** naspram originalnog hand-flexion pristupa
(4 markera šake `zapesce/srednji/mali/palac`). Treba razjasniti:
- Koji **kut** vozimo na robot? (npr. **fleksija lakta** = kut između `podlaktica` i
  `nadlaktica` segmenta; ili fleksija zapešća segment `zapesce` vs `podlaktica`.)
- Definira li to **rigid-body segmente** (svaki s vlastitim frameom/orijentacijom) ili
  pojedinačne markere? O tome ovisi kinematika.

### B. Kad su markeri/segmenti u sceni
1. `sdk_inspect.py` → pročitati **točna imena setova/markera + redoslijed** + pozicije.
2. Na temelju toga:
   - **Marker-set varijanta**: prilagoditi `marker_name_map` i `kinematics.*_marker` u
     `default.yaml`; postojeći `hand_frame`/`flexion_angle` možda dovoljni.
   - **Segment/rigid-body varijanta**: ako Motive daje orijentacije segmenata (kvaternioni),
     kut računati **direktno iz segment-orijentacija** (novi mali kinematics modul:
     kut između dva segment-framea), umjesto cross-product iz markera.
3. Implementirati **`LiveSDKSource`** (MarkerSource/segment-source) na SDK klijentu:
   - unicast, `data_descriptions_listener` (imena), `new_frame_with_data_listener`
     (pozicije/orijentacije) → thread-safe queue → naš `MarkerFrame`/kut.
   - ugraditi u `src.tools.live_sender` (npr. `--sdk` putanja).

### C. Validacija (redom, sigurnosno)
1. **Bridge → pipeline `dry_run`** (BEZ robota): `primljeno>0`, rate ~120 Hz, kut razuman.
2. **Bridge → robot, suženi safety** (`--range-dps 20 --max-speed-dps 15`, kratko),
   prst na e-stopu. Pa protokolske granice → Faza 2 matrica (`02_TEST_PROTOCOL.md`).

## Komande (podsjetnik)
```bash
# provjera veze:
.venv/Scripts/python testing/lab/diag/sdk_probe.py 192.168.40.31 192.168.40.30 0
.venv/Scripts/python testing/lab/diag/sdk_inspect.py 192.168.40.31 192.168.40.30
# robot (kad dođe red), suženo:
.venv/Scripts/python -m src.pipeline.main --sink ur3e --ip 192.168.40.50 \
  --joint 4 --range-dps 20 --max-speed-dps 15 --seconds 10 --external --port 51000
```
