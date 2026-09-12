# 10 — MOTIVE: postavke streaminga i kruta tijela (saka / podlaktica / nadlaktica)

Referenca za podešavanje Motivea tako da naš živi put radi
(**Motive → NatNet SDK → `live_sender --sdk|--arm` → pipeline → UR3e**).
Vrijedi za **Motive 3.0.1 / NatNet 4.0** (klijent: NatNet SDK 4.5 PythonClient).

Adrese: Motive **192.168.40.31** · ovaj PC **192.168.40.30** · robot **192.168.40.50**.

---

## 0) Što kod stvarno zahtijeva (i što mu je svejedno)

| Zahtjev koda | Motive postavka | Bitno? |
|---|---|---|
| Čitamo **rigid body** podatke (`rigid_body_data`), ne markere | **Rigid Bodies = ON** | **KRITIČNO** — bez toga nema nijednog upotrebljivog okvira |
| Tijela tražimo po **stream ID-u**, ne po imenu | `nadlaktica`=**25**, `podlaktica`=**24**, `saka`=**16** | **KRITIČNO** (ili proslijedi `--id-*`) |
| Multicast na labos switchu daje **0 okvira** | **Transmission = Unicast** | **KRITIČNO** |
| SDK klijent se veže na konkretan NIC | Local Interface = **192.168.40.31**, klijent `--client-ip 192.168.40.30` | **KRITIČNO** (PC ima 2 kartice na `.40.x`) |
| Sva 3 tijela moraju biti u **istom okviru** i `tracking_valid` | vidljivost markera, min. marker count | **KRITIČNO** — inače se okvir preskače, a nakon 150 ms lupa fail-safe |
| Kutovi su **relativni na home** (prvi okvir) | Up Axis, jedinice, ishodište scene | **nebitno za matematiku**, ali vidi §3 (kalibracija!) |
| Kut lakta je **scale-invariantan** (kut između 3 ishodišta) | mm vs m | nebitno |
| Kvaternion `(qx,qy,qz,qw)` = NatNet native = scipy konvencija | — | ne dira se |

> Ukratko: Motive mora slati **kruta tijela, unicastom, s točnim stream ID-evima**.
> Sve ostalo je ili kozmetika ili stvar **kalibracije** (`arm_axes`).

---

## 1) Data Streaming pane (Motive: View → Data Streaming)

| Postavka | Vrijednost | Zašto |
|---|---|---|
| **Broadcast Frame Data / Enable** | **ON** | glavni prekidač streama |
| **Local Interface** | **192.168.40.31** | ne ostavljati `loopback`; mora biti labos NIC |
| **Transmission Type** | **Unicast** | multicast je u labosu dao 0 okvira (switch/IGMP) |
| **Rigid Bodies** | **ON** | jedini podatak koji živi izvor koristi |
| **Labeled Markers / Markers** | ON dok dijagnosticiraš | `sdk_inspect.py` po njima ispisuje imena; poslije se smije ugasiti |
| **Unlabeled Markers** | OFF | čista ušteda pojasa i CPU-a |
| **Skeletons / Devices / Force Plates** | OFF | ne koristimo |
| **Up Axis** | **isti kao 2026-06-27 (Motive default Y-Up)** | promjena ne kvari matematiku, ali **poništava predznake u `arm_axes`** |
| **Command / Data Port** | default **1510 / 1511** | SDK klijent očekuje default |
| **Frame rate streama** | **puni 120 Hz** (bez decimacije) | pipeline vrti 125 Hz; svako podsemplovanje izravno gura latenciju gore |
| Remote Trigger / VRPN / Trackd | OFF | nepotrebno |

Firewall na Motive PC-u mora propuštati UDP 1510/1511 prema `192.168.40.30`.

**Kamere/scena**: frame rate **120 Hz**, scena kalibrirana (prihvatljiv mean error),
maske i refleksije očišćene. Rekalibracija kamera **ne** dira `arm_axes`.

---

## 2) Kruta tijela — obavezne postavke po tijelu

Sva tri su **rigid body**, ne skeleton, i svako ima **≥3 markera**, raspoređena
**asimetrično** i **različito među segmentima**, da Motive ne zamijeni tijela.

| Tijelo | Ime (radi dijagnostike) | **Streaming ID** (2026-08-31) | Uloga u kodu |
|---|---|---|---|
| Nadlaktica | `nadlaktica` | **25** | `--id-upper`; rame yaw/pitch (vs svjetski home) |
| Podlaktica | `podlaktica` | **24** | `--id-fore`; lakat + os pronacije (`axial_from_forearm`) |
| Šaka | `saka` | **16** | `--id-hand`; zglob flex/dev |

Po tijelu (Properties pane, odabrano tijelo):

1. **Streaming ID = 25 / 24 / 16** (stanje 2026-08-31; u lipnju je bilo 18/17/16 —
   **provjeri svaki put**, ID se mijenja kad se tijelo napravi iznova). To je jedino
   po čemu ih kod razlikuje — ime je za `--sdk`/`--arm` nebitno. Ako ispadnu drugačiji,
   ne prepravljaj Motive, nego proslijedi `--id-upper/--id-fore/--id-hand`.
2. **Smoothing = 0**, prediction/filtriranje isključeno. Mi filtriramo One-Euro filtrom
   nizvodno i **mjerimo latenciju** — Motiveovo zaglađivanje dodalo bi skriveni lag i
   pokvarilo usporedbu filtara u radu.
3. **Minimum Marker Count = 3** (ne spuštati na 2): tijelo s 2 markera daje nesigurnu
   orijentaciju, a orijentacija nosi 5 od 6 kanala.
4. **Tracking aktivan** — tijelo mora slati `tracking_valid`. Kod **preskače cijeli
   okvir ako ijedno od tri tijela ispadne**, pa okluzija bilo kojeg segmenta zaustavlja
   robota (fail-safe pri starosti signala > 150 ms).
5. **Ishodište (pivot).** Jedino mjesto gdje pozicija tijela ulazi u matematiku je kut
   lakta — kut lomljene linije `nadlaktica → podlaktica → šaka`. Najtočnije je ako
   ishodišta sjede **na zglobovima**: nadlaktica ≈ **rame**, podlaktica ≈ **lakat**,
   šaka ≈ **zapešće**; tada je izračunata vrijednost doslovno kut lakta. Ako su
   ishodišta u težištu markera (default), kut je i dalje monoton i upotrebljiv, ali
   sustavno odstupa od anatomskog — namjesti pivote ako ti u radu treba **apsolutni**
   kut lakta, inače ostavi kako je i budi dosljedan kroz sve runove.
6. **Ne stvaraj tijela iznova** i ne rotiraj im lokalne osi bez rekalibracije (§3).

---

## 3) Što poništava kalibraciju `arm_axes` (i kako je vratiti)

`arm_axes` u `src/config/default.yaml` (Euler `seq`/`idx`/`sign` po segmentu) ovisi
**isključivo o tome kako su definirane lokalne osi krutih tijela i svjetska Up os**.
Rekalibracija je nužna ako se dogodi bilo što od:

- tijelo obrisano i **napravljeno iznova** (nove lokalne osi),
- „reset/align orientation" ili ručni offset orijentacije tijela,
- **promjena Up Axis** (Y-Up ↔ Z-Up) u streamingu,
- markeri premješteni po segmentu toliko da se osi bitno zakrenu,
- mjerenje na **drugoj ruci** (lijeva/desna) — predznaci se okreću.

Rekalibracija (5 min):

```bash
.venv/Scripts/python testing/lab/diag/arm_inspect.py 192.168.40.31 192.168.40.30
```

Drži **ispruženu ruku** dok se ne ispiše `HOME postavljen`, pa izoliraj **jedan po
jedan** pokret (samo rame gore/dolje, samo rame lijevo/desno, samo lakat, samo fleksija
šake, samo devijacija, samo pronacija) i gledaj koja `RAW` komponenta reagira, kojim
predznakom i u kojem rasponu. To upiši u `arm_axes`, pa ponovi i potvrdi da `MAPPED`
kanali reagiraju **svaki na svoj** pokret.

Zadnja kalibracija (2026-06-27, vrijedi ako Motive scena nije dirana):
rame `ZXY` yaw=Z, pitch=X (−1); lakat **orijentacijski** `XYZ` idx 0, sign −1;
zglob `XYZ` flex=X (−1), dev=Y; axial **s podlaktice** (`el_or_Z`).

---

## 4) Provjera redom (2 min, prije svakog runa)

```bash
# 1) veza + broj okvira (službeni SDK, ground truth)
.venv/Scripts/python testing/lab/diag/sdk_probe.py 192.168.40.31 192.168.40.30 0

# 2) imena i STREAM ID-evi — potvrdi 25/24/16
.venv/Scripts/python testing/lab/diag/sdk_inspect.py 192.168.40.31 192.168.40.30

# 3) kanali reagiraju na prave pokrete
.venv/Scripts/python testing/lab/diag/arm_inspect.py 192.168.40.31 192.168.40.30

# 4) most prema pipelineu (6-DOF)
.venv/Scripts/python -m src.tools.live_sender --arm \
  --server-ip 192.168.40.31 --client-ip 192.168.40.30 \
  --id-upper 25 --id-fore 24 --id-hand 16 --port 51000
```

| Simptom | Uzrok |
|---|---|
| `Nema rigid-body okvira 2 s` | Rigid Bodies OFF, krivi Local Interface, ili multicast umjesto unicasta |
| `Nedostaju rigid bodies [..]` | krivi stream ID-evi ili je segment okludiran |
| Stream radi, robot stoji | fail-safe: okviri stižu isprekidano (okluzija) — starost signala > 150 ms |
| Kanal reagira na krivi pokret | `arm_axes` ne odgovara trenutnim tijelima → §3 |
| Sve radi pa naglo 0 okvira | druga kartica (`Ethernet 4`, `.22`) preuzela rutu — koristi `--client-ip 192.168.40.30` |

Puni protokol sesije: **`09_PLAN_SESIJE.md`** (B1). Mrežna dijagnostika: `diag/README.md`.
