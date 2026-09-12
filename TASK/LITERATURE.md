# LITERATURE — analiza i sinteza (Stage 1)

> Pregled literature za seminar "Upravljanje zglobom UR robota pomoću OptiTrack sustava u
> realnom vremenu". Svrha: (a) Related Work, (b) **opravdanje izbora metoda**, (c) **usporedba
> s vlastitim rješenjem** (zahtjev kolegija: literatura *korištena*, ne samo citirana).
> Citatni ključevi iz `docs/references.bib` / `rag query`. RAG indeks: **13 PDF-ova, 567 chunkova**.
> Pravilo kolegija: ≥5 radova, ≥2021, IEEE/Springer/Elsevier/ACM. **Imamo 12 kvalificiranih
> radova s PDF-om** (+1 potporni MDPI) — pokrivaju sve dijelove seminara.

## Korpus (preuzeti PDF-ovi)

| Cite key | Rad (skraćeno) | Venue, god. | Dio seminara | Kval.* |
|----------|----------------|-------------|--------------|--------|
| `ghanbarzadeh2025` | Variable impedance control prema ISO/TS 15066 | Springer IJIDeM, 2024 | Sigurnost | ✓ |
| `peng2025` | Dynamic Speed & Separation Monitoring (binocular vision) | Springer JIRS, 2025 | Sigurnost | ✓ |
| `wang2025` | Transparent & stable bilateral teleop. pod mrežnim kašnjenjem | Springer IJSR, 2024 | Latencija/rasprava | ✓ |
| `louca2024` | Haptic feedback u high-latency teleoperaciji (0–2600 ms) | ACM THRI, 2024 | Latencija/rasprava | ✓ |
| `shi2025` | Latency & reliability optimizacija WebRTC teleop. (real-time) | IEEE Access, 2025 | Komunikacija/latencija | ✓ |
| `zainudin2025` | Enhanced teleop. master-slave + multithreading (UR10e) | IEEE Access, 2025 | Komunikacija/UR | ✓ |
| `weigend2023` | Human arm pose (smartwatch) → robot control | IEEE IROS, 2023 | Mapiranje pokreta | ✓ |
| `weigend2024` | iRoCo: intuitivno upravljanje robotom sa smartwatcha | IEEE ICRA, 2024 | Mapiranje/autonomija | ✓ |
| `martini2024`† | Robustan real-time filter za HRI tracking (vs Kalman) | IEEE RO-MAN, 2024 | Filtriranje | ✓ |
| `stroppa2023` | Shared-control teleoperation paradigme | Springer JIRS, 2023 | Teleop.↔autonomija | ✓ |
| `glawe2026` | Human autonomy & sense of agency u HRI (sustavni pregled) | Springer IJSR, 2026 | pHRI rasprava | ✓ |
| `castillo2025` | Smartphone mocap vs **OptiTrack** (točnost gaita) | Springer Exp. Tech., 2025 | Eksp. postav / mocap | ✓ |
| `zhu2022`† | IMU mocap + adaptivna atenuacija tremora | MDPI Sensors, 2022 | Filtriranje (potporni) | ✗ MDPI |

\* zadovoljava tvrdi venue+godina zahtjev. † `martini2024`, `zhu2022` još nemaju unos u
`docs/references.bib` → dodati pri pisanju (`rag cite`/`--file`).

**Paywalled (samo metapodaci u `SOURCES_LOG.md`, citirati ako se osigura pristup):**
Mechatronics 2022 (collision detection, Elsevier) · TCSVT 2022 (hand-motion mapping survey,
IEEE) · RCAR 2023 (joint-Cartesian mapping, IEEE) · M2VIP 2024 (usporedba filtara, IEEE) ·
IEEE Sensors Letters 2023 (marker mocap točnost) · **Lindvig 2025 `ur_rtde` (IEEE SII)** —
referentni rad za alat koji koristimo; citirati i bez PDF-a.

---

## Mapiranje literature na sekcije znanstvenog rada (TASK.md §F)

| Sekcija rada | Ključni izvori |
|---|---|
| Uvod / Related Work | svi (pregled pHRI, teleoperacija, sigurnost) |
| Metodologija — komunikacija (UDP/TCP, latencija) | `shi2025`, `zainudin2025`, `wang2025` |
| Metodologija — algoritmi (filtriranje) | `martini2024`, `zhu2022`, (M2VIP meta) |
| Metodologija — mapiranje pokreta | `weigend2023`, `weigend2024`, (TCSVT/RCAR meta) |
| Eksperimentalni postav — hardver/mocap | `castillo2025` (OptiTrack točnost), (Siaw meta) |
| Eksperimentalni postav — sigurnosni protokoli | `ghanbarzadeh2025`, `peng2025` |
| Rezultati i analiza — latencija/jitter | `shi2025`, `zainudin2025`, `louca2024` |
| Rasprava — teleop.↔autonomija, osjećaj kontrole | `glawe2026`, `stroppa2023`, `louca2024`, `wang2025` |

---

## Sinteza po temama (problem → metoda → kako koristimo)

### Sigurnost (pHRI / cobot)
- **`ghanbarzadeh2025`**: ISO/TS 15066 Power-and-Force-Limiting — max. dopuštena brzina iz
  efektivne mase/sile/krutosti; variable-impedance regulator. **Koristimo:** opravdava naš
  sigurnosni pipeline (speed/range limiting kao softverski surogat PFL-a). **Usporedba:** naš
  clamp je jednostavniji od impedancije — svjestan kompromis za 1-zglob demo.
- **`peng2025`**: dinamički **Speed & Separation Monitoring** (SSM) — brzina robota ovisi o
  udaljenosti čovjeka. **Koristimo:** koncept za fail-safe i argument da sigurnost ovisi o
  kontekstu blizine; u Raspravi kao naprednija nadogradnja našeg statičkog limita.

### Latencija / jitter / osjećaj kontrole
- **`wang2025`**: stabilnost ↔ transparentnost kompromis pod vremenski-promjenjivim kašnjenjem.
- **`louca2024`**: dvosmjerna kašnjenja **0/600/1500/2600 ms**; izvedivost pada s kašnjenjem.
- **`shi2025`** (IEEE Access): real-time teleoperacija s optimizacijom latencije/pouzdanosti
  preko mreže (WebRTC, force feedback) — konkretne mrežne metrike.
- **Koristimo (metrika/prag):** definira što mjerimo (§D.3) i prag interpretacije (§D.4);
  ciljamo **end-to-end < ~100 ms** (lokalni UDP→RTDE put → red veličine brži od ovih mrežnih
  scenarija). **Usporedba:** naš jitter prema njihovim pragovima izvedivosti.

### Mapiranje / retargeting pokreta + UR upravljanje
- **`weigend2023`, `weigend2024`**: kontinuirano mapiranje poze ljudske ruke na upravljanje
  robotom iz oskudnih senzora (smartwatch), uz zaglađivanje. **Koristimo:** kontekst za naš
  izračun orijentacije šake → 1 rotacijska komponenta (fleksija) → UR3e wrist_1/J4.
- **`zainudin2025`** (IEEE Access): master-slave teleoperacija UR10e s **multithreadingom**,
  smanjenje latencije ~91%. **Koristimo:** potvrđuje našu arhitektonsku odluku o
  **producer/consumer niti** i RTDE-pristupu za nisku latenciju na UR-u. **Usporedba:** naš
  cilj je 1-DOF deterministički put umjesto pune teleoperacije.
- **Usporedba (općenito):** naš pristup je namjerno 1-DOF, direktan (bez IK/učenja) — manje
  općenit, ali niskolatentan i lakše sigurnosno ograničiv.

### Real-time filtriranje šumnog pokreta
- **`martini2024`** (IEEE): real-time filter pipeline, **smanjenje jittera robota**, usporedba
  vs linearni Kalman 1./2. reda.
- **`zhu2022`** (potporni): tremor **6–15 Hz**; klasični low-pass unosi **fazno kašnjenje
  nepovoljno za real-time** → adaptivni filtar. **Koristimo (KLJUČNO):** opravdava zamjenu
  nekauzalnog Savitzky-Golay (~1–2 s lag) **One-Euro filtrom** (+ Butterworth/EMA usporedba).
  **Usporedba:** radimo istu lag-vs-šum analizu kao Martini (vs Kalman) i Zhu (vs fixed-gain).

### Teleoperacija ↔ autonomija / osjećaj kontrole (pHRI rasprava)
- **`stroppa2023`**: **shared-control** paradigme teleoperacije — spektar između ručnog i
  autonomnog. **`glawe2026`**: sustavni pregled **ljudske autonomije i sense of agency** u HRI.
  **Koristimo:** okosnica §D.4 rasprave (granica teleoperacija↔autonomija, kada čovjek gubi/
  zadržava osjećaj kontrole). **Usporedba:** naš sustav je čista (unilateralna) teleoperacija
  bez dijeljene autonomije — pozicioniramo ga na tom spektru i diskutiramo posljedice.

### Mocap (OptiTrack) — eksperimentalni postav
- **`castillo2025`**: usporedba jeftinog mocapa s **OptiTrack** referencom (točnost gaita).
  **Koristimo:** potkrepljuje OptiTrack kao točan referentni izvor i kvantificira očekivani
  red veličine šuma/točnosti za naš eksperimentalni postav.

---

## Iz literature izvedeni (provizorni) tehnički parametri

| Parametar | Vrijednost (provizorno) | Opravdanje |
|---|---|---|
| Cilj end-to-end latencije | **< ~100 ms** (median), nizak jitter | `louca2024`, `wang2025`, `shi2025` |
| Primarni filter | **One-Euro** (min_cutoff ~1 Hz, β ~0.007 — tune) | `zhu2022`, `martini2024` |
| Usporedni filtri | Butterworth IIR 2. red (~5–8 Hz), EMA | `martini2024`, `zhu2022` |
| Pojas: voljni pokret vs šum | voljni < ~2–3 Hz; tremor/šum 6–15 Hz | `zhu2022` |
| Granica brzine J4 | konzervativno ≤ **30–45 °/s** (početno) | `ghanbarzadeh2025` (PFL), `peng2025` (SSM) |
| Range-clamp J4 | ±N° oko home (definirati pri tuningu) | `ghanbarzadeh2025` |
| Fail-safe timeout | gubitak signala > ~100–200 ms → zaustavljanje | `louca2024` + sigurnost |
| Arhitektura niske latencije | producer/consumer niti, RTDE | `zainudin2025` |

> Finalizirati pri tuningu (Stage 3/4), potkrijepiti izmjerenim podacima.

## Praznine i napomene
- **Tema F** (kut zgloba iz markera, vektorska metoda) nema kvalificirani OA rad (najbolji,
  IEEE Sensors Letters 2023, paywalled). Naša kinematika je standardna vektorska metoda →
  ne ovisi o citatu; kontekst pokrivaju `weigend2023/2024`, `zhu2022`.
- **One-Euro original** (Casiez et al., *1€ Filter*, ACM CHI **2012**) — citirati kao
  algoritamsku referencu, ne broji se u ≥2021 zahtjev.
- **`ur_rtde`** (Lindvig 2025, IEEE SII) — referentni rad za alat; citirati i bez PDF-a.
- Pri `docs/references.bib`: dodati `file`-povezane unose za `martini2024` i `zhu2022`;
  provjeriti godine (npr. `ghanbarzadeh`/`wang` online-first vs vol-godina).
