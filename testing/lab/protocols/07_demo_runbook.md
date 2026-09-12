# 07 — DEMO RUNBOOK (ručno pokretanje pred profesorima)

Korak-po-korak za živu demonstraciju: **OptiTrack → puna 6-DOF mimikrija ruke → UR3**.
Sve komande se pokreću **iz korijena repozitorija** (`hri-seminar`), u PowerShellu.
Python je uvijek **`.venv/Scripts/python.exe`**.

> Cilj: čovjek u volumenu miče rukom, robot vjerno oponaša **rame, lakat i šaku**
> (zglob-na-zglob mimikrija, bez inverzne kinematike).

---

## 0. Brza referenca (za uvježbanog operatera)

Trebaš **dva terminala**. Bridge se NE gasi sam (pusti ga u Terminalu A).

```powershell
# TERMINAL A — most OptiTrack -> UDP (pusti da radi cijelo vrijeme):
.venv/Scripts/python.exe -m src.tools.live_sender --arm --server-ip 192.168.40.31 --client-ip 192.168.40.30 --id-upper 25 --id-fore 24 --id-hand 16 --port 51000

# TERMINAL B — pipeline na PRAVOM robotu (uske granice za prvi prolaz):
.venv/Scripts/python.exe -m src.pipeline.main --mode multi_joint --sink ur3e --ip 192.168.40.50 --range-dps 15 --max-speed-dps 12 --seconds 60 --external --port 51000 --latency-csv data/raw/lab_session_01092026_020000/telemetry/demo.csv
```

Detaljno niže. **Prsti na e-stopu tijekom svakog pokreta robota.**

---

## 1. Oprema i mreža (poznata, potvrđena konfiguracija)

| Uloga | IP | Napomena |
|---|---|---|
| Ovaj PC (klijent) | `192.168.40.30` | NIC **Ethernet** na labos mreži |
| Motive (OptiTrack) | `192.168.40.31` | Motive 3.0.1, NatNet 4.0 |
| Robot **UR3e** | `192.168.40.50` | PolyScope 5.9.5, RTDE + **Remote Control mod** |
| URSim (rezerva) | `192.168.208.128` | e-Series sim, treba *Remote Control* |

- Svi uređaji na **istom switchu**.
- ⚠️ PC ima i drugu karticu `Ethernet 4` (`192.168.40.22`) na istoj podmreži —
  **idealno je ugasiti** da ne muti rutiranje (inače radi, ali oprez).
- Rigid bodyji u Motiveu: **`nadlaktica` ID=18, `podlaktica` ID=17, `saka` ID=16**.

### Provjera mreže
```powershell
ping 192.168.40.31   # Motive
ping 192.168.40.50   # robot
```

---

## 2. Motive (OptiTrack) — streaming

U Motiveu (na PC-u `.31`):
1. **Data Streaming = ON**, Local Interface = **192.168.40.31**.
2. **Transmission Type = Unicast** (multicast je u ovom labosu davao 0 okvira!).
3. **Stream Rigid Bodies = ON**.
4. U 3D viewu provjeri da su sva tri rigid bodyja **tracked / vidljiva** (ne sivi/izgubljeni).

### Provjera veze (službeni SDK ground-truth)
```powershell
.venv/Scripts/python.exe testing/lab/diag/sdk_probe.py 192.168.40.31 192.168.40.30 0
```
Očekuješ: `connected() -> True`, `MotiveVer -> [3,0,1,...]`, **`frames/3s -> ~360`** (120 Hz).

---

## 3. Robot UR3 — priprema

1. Uključi robot, **otpusti kočnice** (brake release) na privjesku.
2. Postavi ruku robota u **sigurnu početnu pozu** (uspravno, dalje od limita i prepreka).
   Pipeline uzima **trenutnu pozu kao "home"**, pa od nje robot kreće micati zglobove.
   - Najlakše: na privjesku **Freedrive** → ručno namjesti → pusti.
3. UR3e **treba** "Remote Control" mod (☰ → Settings → System → Remote Control →
   Enable, pa gornji desni prekidač → *Remote*). (Stari CB3 na `.27` ga nije imao.)
4. **Očisti prostor** oko robota (envelope ovisi o granicama; ±15° je umjeren zamah).

### Provjera RTDE veze (samo čitanje, bez gibanja)
```powershell
.venv/Scripts/python.exe -m src.tools.check_ursim --ip 192.168.40.50 --no-move
```
Očekuješ: `Povezano. Robot mode=7 safety mode=1` i ispis trenutnih zglobova.

---

## 4. Pokreni MOST (Terminal A)

Most čita OptiTrack (NatNet SDK) i šalje 6 kanala kuta na UDP `:51000`.
**Pusti ga da radi cijelo vrijeme demonstracije** (ne gasi se sam).

```powershell
.venv/Scripts/python.exe -m src.tools.live_sender --arm --server-ip 192.168.40.31 --client-ip 192.168.40.30 --id-upper 25 --id-fore 24 --id-hand 16 --port 51000
```
- U logu vidiš `axes={...}` (učitana kalibracija) i `Šaljem markere -> 127.0.0.1:51000`.
- Ako piše `Nedostaju rigid bodies ... vidljivi: []` → **uđi u volumen**; most šalje
  tek kad su sva tri tijela vidljiva.

> ℹ️ Ignoriraj brbljave `MoCap Frame: N` retke — to ispisuje SDK, bezopasno.
>
> ⚠️ **Pokreni TOČNO JEDAN most na port `:51000`.** Dva mosta istovremeno (npr.
> zaboravljen stari terminal) šalju duplikate → prijem skoči na ~240 Hz, a statistika
> prijema prijavi lažni "gubitak"/reorder (npr. 38% u `demo.summary.json`). Prije
> pokretanja zatvori sve ranije `live_sender` procese.

---

## 5. (Preporučeno) Suha proba bez robota

Prije robota provjeri da svih 6 kanala teče. **Stani u volumen, ispruži ruku**, pa:
```powershell
.venv/Scripts/python.exe -m src.pipeline.main --mode multi_joint --sink dry_run --seconds 6 --external --port 51000
```
Očekuješ: `primljeno>0`, **rate ~120 Hz, 0.00% gubitka**, i retke
`t=..s Δzglob[deg]: base=.. shoulder=.. elbow=.. wrist_1.. wrist_2.. wrist_3..`.
Pomakni svaki segment i provjeri da se mijenja odgovarajući kanal.

---

## 6. Pokreni PIPELINE na robotu (Terminal B)

⚠️ **Prst na e-stopu.** Čovjek stoji **neutralno (ispružena ruka)** dok pipeline
ne uhvati home (~3 s), pa kreće **polako i s malim otklonima**.

**Prvi prolaz — uske granice (±15°, 12°/s):**
```powershell
.venv/Scripts/python.exe -m src.pipeline.main --mode multi_joint --sink ur3e --ip 192.168.40.50 --range-dps 15 --max-speed-dps 12 --seconds 60 --external --port 51000 --latency-csv data/raw/lab_session_01092026_020000/telemetry/demo.csv
```
Kad si siguran, **postupno proširi** (i dalje konzervativno):
```powershell
# srednje granice:
... --range-dps 25 --max-speed-dps 18 ...
# pune per-zglob granice iz configa (izostavi --range-dps/--max-speed-dps):
.venv/Scripts/python.exe -m src.pipeline.main --mode multi_joint --sink ur3e --ip 192.168.40.50 --seconds 90 --external --port 51000 --latency-csv data/raw/lab_session_01092026_020000/telemetry/demo.csv
```

Pipeline svake ~1 s ispisuje **Δ po zglobu** (i `[HOLD]` kad je fail-safe aktivan).
Na kraju ispisuje latenciju i statistiku prijema.

---

## 7. Scenarij demonstracije (što raditi rukom)

Mapiranje **ljudski pokret → robotski zglob**. Radi **jedan po jedan, polako**;
između pokreta vrati ruku u neutralu.

| # | Pokret čovjeka | Robotski zglob |
|---|---|---|
| 1 | rame **lijevo/desno** (rotacija) | **base** (J1) |
| 2 | rame **gore/dole** | **shoulder** (J2) |
| 3 | **lakat** gore/dole | **elbow** (J3) |
| 4 | šaka **gore/dole** (fleksija) | **wrist_1** (J4) |
| 5 | šaka **lijevo/desno** (devijacija) | **wrist_2** (J5) |
| 6 | šaka **rotacija oko osi** (pronacija) | **wrist_3** (J6) |

Za efektan finiš: spori **kombinirani** pokret cijele ruke.

💡 **Drži markere/segmente okrenute prema kamerama** — ako nestanu iz polja,
pipeline aktivira fail-safe (`[HOLD]`, zglob se zamrzne) i robot "stane".

---

## 8. Sigurnost (uvijek)

- **E-stop na dohvat ruke** tijekom svakog gibanja robota.
- **Ctrl-C** u Terminalu B uredno zaustavi servo i prekine vezu.
- Granice (`--range-dps`/`--max-speed-dps`) **kapiraju SVAKI zglob** — počni usko.
- **Fail-safe**: gubitak signala > 150 ms → zglob drži zadnju vrijednost (ne divlja).
- Nitko u dosegu robota dok se miče.

---

## 9. Gašenje

1. Terminal B: pipeline sam završi nakon `--seconds`, ili **Ctrl-C**.
2. Terminal A: **Ctrl-C** za gašenje mosta.
3. Robot ostaje gdje je; po želji vrati u home (Freedrive) i uključi kočnice.

---

## 10. Troubleshooting

| Simptom | Uzrok / rješenje |
|---|---|
| `Nije primljen nijedan marker-frame` | Most ne šalje. Provjeri Terminal A; jesi li u volumenu; jesu li sva 3 rigid bodyja tracked. |
| Most: `vidljivi: []` | Tijela izvan kamera ili Motive ne streama rigid bodye. Uđi u volumen / provjeri Motive (korak 2). |
| `frames/3s -> 0` u sdk_probe | Motive streaming OFF, krivi interface, ili multicast umjesto **unicast**. |
| `Please enable remote control` | Vrijedi i za **URSim** i za lab **UR3e** (`.50`): PolyScope ☰ → Settings → System → Remote Control → Enable, pa gore desno prebaci na *Remote*. |
| Robot se ne miče | Krivi `--ip`/`--sink`; robot ne u mode 7; pipeline 0 frameova; granice 0. Provjeri korak 3 i 5. |
| Puno `[HOLD]`, rate < 110 Hz | **Okluzija** markera. Drži segmente prema kamerama, smiri pokrete. |
| Rate ~**240 Hz**, visok "gubitak"/reorder | **Dva mosta** na istom portu (duplikati). Ugasi sve stare `live_sender` procese, ostavi jedan. |
| Zglob ide u **krivom smjeru** | Okreni predznak u `src/config/default.yaml` → `arm_axes` (`*_sign`/`signs`) i **restartaj most** (Terminal A). |
| Pogrešna mreža / robot nedostupan | Provjeri da je `Ethernet` NIC na `192.168.40.30`; ugasi `Ethernet 4` (`.22`). |

---

## 11. (Samo ako se promijeni scena) Rekalibracija osi

Kalibracija je već u `src/config/default.yaml` (`arm_axes`). Ponovi **samo** ako
prerasporediš markere/rigid bodye ili im promijeniš lokalne osi:
```powershell
.venv/Scripts/python.exe testing/lab/diag/arm_inspect.py 192.168.40.31 192.168.40.30
```
Radi **jedan izolirani pokret po jedan**, gledaj koja `RAW` komponenta reagira
(+ predznak), i upiši u `arm_axes`. Zatim **restartaj most**. (Detalji pristupa:
`testing/lab/protocols/06_live_optitrack.md`.)

---

### Rezerva: demo na URSimu (bez pravog robota)
Sve isto, samo pipeline cilja URSim i treba mu *Remote Control* mod:
```powershell
.venv/Scripts/python.exe -m src.pipeline.main --mode multi_joint --sink ursim --ip 192.168.208.128 --seconds 60 --external --port 51000
```
