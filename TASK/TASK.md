# TASK — Seminar: Upravljanje zglobom UR robota pomoću OptiTrack sustava u realnom vremenu

> **Kolegij:** Interakcija čovjeka i robota · **Tip:** Seminar (Zadatak 2)
> **Strategija:** Varijanta B preko A — prvo izgraditi stabilan real-time sustav na
> URSim-u (Var. A, 40 bod), zatim ga proširiti na stvarni UR3e robot sa sigurnosnim
> pipelineom i pHRI analizom (Var. B, 60 bod).
>
> Ovaj dokument je **radni vodič** koji vodi cijelu izradu. Korake izvode specijalizirani
> agenti (vidi §G). Ažuriraj checkboxove kako napreduješ.

---

## A. Pregled i bodovanje

| Varijanta | Razina | Bodovi | Fokus |
|---|---|---|---|
| A | srednje lakša | 40 | Komunikacija, obrada signala, stabilnost — **simulacija (URSim)** |
| B | napredna | 60 | Stvarni UR3e + višeslojna sigurnost + latencija/jitter + **pHRI rasprava** |

**Zajednički okvir (oba zadatka):** sustav u realnom vremenu (1) prima pozicije markera
ljudske ruke iz OptiTrack-a, (2) računa zakret odabranog ljudskog zgloba, (3) mapira ga na
jedan zglob UR robota, (4) šalje vrijednosti robotu mrežom, (5) radi kontinuirano uz jasno
definirane granice sigurnog ponašanja.

**Mapirani ljudski zglob → UR zglob (prijedlog):** zakret zapešća (wrist) ili lakta iz
markera šake → UR zglob `wrist_3` (J6) ili `elbow` (J3). Odabir fiksirati u `config.yaml`.

### Predaja (zahtjevi kolegija)
- **Tehnički izvještaj** u formi **znanstvenog rada (LaTeX, `fsb-paper`, STROGO max 12 str.)**
  — detaljna dokumentacija procesa razvoja, uključujući **kod, konfiguraciju i korake za
  postavljanje**.
- **Demonstracija praktičnog dijela u laboratoriju** (live prikaz sustava).
- **Rok:** 3 dana prije ispitnog roka za koji se prijavljuje ispit.

### Zajednički okvir za sve seminare (OBAVEZNO)
- Obavezna **implementacija + evaluacija**.
- **Pregled literature:** **min. 5 znanstvenih radova**, **ne stariji od 5 godina**
  (≥ 2021), izvori **IEEE / Springer / Elsevier / ACM**.
- Literatura mora biti **korištena, ne samo citirana**: u opisu odabira metode **i** u
  usporedbi s vlastitim rješenjem.
- Fokus na **interakciju čovjek–robot**.

---

## B. Arhitektura sustava (izvor/odredište-agnostična)

**Ključno načelo:** isti kod radi i s reproduciranom snimkom (sada) i sa živim hardverom
(finalno). Zamjena izvora i odredišta je promjena `config.yaml`, ne prepisivanje koda.

```
  OptiTrack izvor          obrada (real-time)                       robot odredište
 ┌───────────────┐   ┌──────────┬────────────┬────────┬────────┐   ┌──────────────┐
 │ replay_source │   │          │            │        │        │   │ ursim_backend│
 │   (CSV→UDP)   ├──►│ receiver │ joint_angle│ filter │ safety ├──►│      ili     │
 │      ili      │   │  (UDP)   │ (vekt. kut)│(kauzal.)│(limiti)│   │ ur3e_backend │
 │ live_source   │   │          │            │        │        │   │   (RTDE)     │
 │ (NatNet/UDP)  │   └────┬─────┴─────┬──────┴───┬────┴───┬────┘   └──────────────┘
 └───────────────┘        ▼           ▼          ▼        ▼
                     ┌──────────────────────────────────────┐
                     │  latency logger (timestamp po fazi)   │
                     └──────────────────────────────────────┘
```

Predložena struktura `src/`:

```
src/
├── config.yaml              # izvor (replay|live), odredište (ursim|ur3e), IP, zglob, limiti, filter
├── source/
│   ├── base.py              # MarkerSource sučelje: yield (seq, t, {marker: xyz})
│   ├── replay_source.py     # čita OptiTrack CSV, re-emitira kao UDP na 120 Hz (seq+timestamp)
│   └── live_source.py       # živi OptiTrack/Motive stream (NatNet/UDP)
├── receiver.py              # UDP prijem; detekcija gubitka/redoslijeda (seq); freq. analiza
├── joint_angle.py           # ≥3 markera/segment → vektorski kut; singularnosti; osjetljivost
├── filter.py                # moving average + low-pass (+ One-Euro za real-time)
├── safety.py                # rate limit, range/workspace clamp, fail-safe, e-stop
├── robot/
│   ├── base.py              # RobotSink sučelje: set_joint(idx, angle) / step()
│   ├── ursim_backend.py     # RTDE prema URSim kontejneru
│   └── ur3e_backend.py      # RTDE prema stvarnom UR3e
├── latency.py               # mjerenje end-to-end latencije + jitter, izvoz CSV/PNG
└── main.py                  # sastavlja pipeline iz config.yaml, glavna real-time petlja
```

**Ponovna upotreba (iz `…/interakcija-covjeka-i-robota/vjezbe_optitrack/src/`):**
- `02_lokalni_koordinatni_sustav.py`: `load_optitrack_data` (parsiranje CSV headera, 6
  redaka, markeri `zapesce/palac/srednji/mali`, 120 fps), cross-product koord. sustav,
  `rotation_matrix_to_angle_axis` (rješava singularnost θ≈0 i θ≈π), Savitzky-Golay.
- `03_to_robot.py`: `URRobotController` (movej/servoj/speedl, dashboard, scale/downsample,
  `MAX_POSITION`/`MAX_ROTATION` limiti) → **nadograditi na RTDE** (`servoJ`/`speedJ`) za
  deterministički real-time umjesto secondary-interface slanja.
- `01_filtering.py`, `prikaz.py`: filtriranje i 3D vizualizacija.

> Postojeći vježbovni kod je **offline batch replay** (cijela CSV → URScript). Seminar
> traži **streaming real-time**: prerada u producer/consumer petlju s fiksnim taktom.

---

## C. FAZA 1 — Varijanta A (URSim, 40 bod)

Mapirano 1:1 na 5 faza iz teksta zadatka. Deliverable: radni URSim demo + grafovi/mjerenja.

### C.1 Prijem podataka iz OptiTrack-a (UDP)
- [ ] `replay_source.py`: učitaj OptiTrack CSV (vježbe snimke) i emitiraj kao UDP datagrame
      sa sekvencijskim brojem + timestampom, na izvornih 120 Hz.
- [ ] `receiver.py`: prijem pozicija **više markera** u realnom vremenu.
- [ ] Identifikacija relevantnih markera za praćenje ruke (`zapesce/palac/srednji/mali`).
- [ ] Obrada **gubitka paketa** i **nepravilnog redoslijeda** (seq broj, buffer, drop/hold).
- [ ] Analiza **frekvencije uzorkovanja** i njezine **stabilnosti** (histogram inter-arrival).
- [ ] Dokumentirati **strukturu primljenih podataka** i način obrade (za izvješće).

### C.2 Izračun zakreta zgloba
- [ ] Koristiti **≥3 markera po segmentu** (vektorski pristup).
- [ ] Matematički ispravan izračun kuta (dot/atan2 između vektora segmenata).
- [ ] Obrazložiti **koji koordinatni sustav** se koristi (lokalni sustav šake, cross-product).
- [ ] Riješiti **singularnosti / nestabilne konfiguracije** (kolinearni markeri, θ≈0/π).
- [ ] **Analiza osjetljivosti** izračuna na pogreške mjerenja (perturbacija markera ±ε).

### C.3 Filtriranje i obrada signala
- [ ] Implementirati **≥1 filter** (pomični prosjek / low-pass; preporuka: **One-Euro**
      za dobar real-time kompromis odziv↔šum).
- [ ] **Analiza utjecaja** filtriranja na **kašnjenje i stabilnost**.
- [ ] **Usporedba** sirovih i filtriranih podataka (graf, RMS šuma uklonjenog filtriranjem).

### C.4 Upravljanje URSim simulatorom
- [ ] Pokrenuti **URSim** (Docker/VM), spojiti `ursim_backend.py` preko **RTDE**.
- [ ] Mapirati izračunati ljudski kut na **jedan UR zglob** (`servoJ`/`speedJ`).
- [ ] **Stabilno upravljanje bez oscilacija**; **ograničenje brzine promjene kuta** (rate limit).
- [ ] **Sigurno ponašanje pri gubitku podataka** (fail-safe: hold zadnju vrijednost / zero velocity).
- [ ] Demonstrirati **kontinuirani rad bez destabilizacije** simulacije (dulji run).

### C.5 Analiza i evaluacija (Var. A)
- [ ] **Kašnjenje** od ljudskog pokreta do reakcije robota (end-to-end).
- [ ] **Stabilnost** upravljanja kroz vrijeme.
- [ ] **Osjetljivost** sustava na nagle promjene pokreta (step/impuls test).

---

## D. FAZA 2 — Varijanta B (stvarni UR3e, 60 bod)

> Pretpostavlja prijelaz na pun hardver: živi OptiTrack stream (`live_source.py`) + stvarni
> **UR3e** (`ur3e_backend.py`). Zahvaljujući agnostičnoj arhitekturi (§B), jezgra pipelinea
> ostaje ista.

### D.1 Integracija sa stvarnim UR robotom
- [ ] `ur3e_backend.py` preko odgovarajućeg sučelja (**RTDE** preporučeno; alternativa URScript/TCP).
- [ ] Stabilno i **glatko upravljanje bez trzaja** (servoJ s lookahead/gain tuning).
- [ ] **Sinkronizacija frekvencije** OptiTrack (120 Hz) ↔ robota (RTDE 500 Hz UR3e) — resampling/takt.
- [ ] Checklist URSim→UR3e (IP, payload, TCP, sigurnosne postavke PolyScope).

### D.2 Sigurnosni pipeline (višeslojni, OBAVEZNO)
- [ ] **Ograničenje maksimalne brzine zgloba** (joint velocity clamp).
- [ ] **Ograničenje dopuštenog raspona gibanja** (workspace/joint range limit).
- [ ] **Fail-safe pri gubitku signala** (timeout → kontrolirano zaustavljanje).
- [ ] **Emergency stop** mehanizam (softverski + veza na hardverski e-stop).
- [ ] Obrazložiti **zašto su odabrane granice** i kako utječu na interakciju.

### D.3 Analiza latencije i jittera
- [ ] Mjerenje **ukupne latencije** sustava (OptiTrack → obrada → robot reakcija).
- [ ] **Varijacije kašnjenja (jitter)** — distribucija, p95/p99.
- [ ] Utjecaj **mrežne komunikacije** (UDP) na stabilnost upravljanja.
- [ ] **Grafički prikaz + interpretacija** u pHRI kontekstu.

### D.4 pHRI analiza i rasprava (jezgra seminara)
- [ ] Kako **kašnjenje utječe na osjećaj kontrole**.
- [ ] Kada sustav postaje **"neugodan" ili nesiguran** za korisnika.
- [ ] Koje su pogreške **prihvatljive**, a koje **nisu**.
- [ ] Granica između **teleoperacije i autonomnog** ponašanja robota.
- [ ] **Povezati s recentnom literaturom** iz pHRI i sigurnosti kolaborativnih robota (§E).

---

## E. Literatura (RAG workflow)

**Obavezan redoslijed: `data_fetcher` → `writer`.** Writer ne piše dok PDF-ovi nisu u
`data/sources/` i ingestirani (`rag ingest`). Citati **isključivo** preko `rag query` —
nikad izmišljen `\cite` ključ.

**Tvrdi zahtjevi kolegija:**
- [ ] **Minimalno 5 znanstvenih radova** (ciljaj 6–8 za sigurnost).
- [ ] Svaki rad **ne stariji od 5 godina** (≥ **2021**).
- [ ] Izvori isključivo **IEEE / Springer / Elsevier / ACM**.
- [ ] Svaki citirani rad mora biti **stvarno korišten u tekstu**: (a) u obrazloženju
      odabira metode **i** (b) u usporedbi s vlastitim rješenjem (Related Work + Rasprava).

Teme za `data_fetcher` (preuzeti PDF → `data/sources/`, logirati u `data/SOURCES_LOG.md`):
- [ ] pHRI sigurnost kolaborativnih robota (recentni pregledni/empirijski radovi, ≥2021).
- [ ] Teleoperacija i **utjecaj latencije/jittera na osjećaj kontrole / transparentnost** (≥2021).
- [ ] Optical motion capture (OptiTrack/Motive **NatNet**) u HRI primjenama (≥2021).
- [ ] Mapiranje ljudskog pokreta na robota / motion retargeting u pHRI (≥2021).
- [ ] Real-time filtriranje za interaktivne sustave (npr. **One-Euro filter** i novije) (≥2021).
- [ ] (Norme kao **ISO/TS 15066**, **ISO 10218** smiju se citirati kao kontekst, ali se
      **ne broje** u 5 znanstvenih radova — nisu IEEE/Springer/Elsevier/ACM članci.)

---

## F. Struktura izvješća — znanstveni rad (LaTeX `fsb-paper`, **max 12 str.**)

Kreira `latex_architect` na "počni pisati". **Obavezna struktura znanstvenog rada**
(prema uputama kolegija) — mapirana na sadržaj ovog projekta:

1. **Sažetak (Abstract)** — problem, pristup, rezultati (sažeto).
2. **Uvod** — motivacija pHRI; **arhitektura sustava** (izvor/odredište-agnostičan pipeline,
   §B); **Pregled povezanih radova (Related Work)** — ≥5 recentnih radova, §E.
3. **Metodologija** — HRI kontekst/motivacija/primjena; korišteni algoritmi (vektorski
   izračun kuta, koordinatni sustav, filtriranje/One-Euro, mapiranje na UR zglob);
   **komunikacija (UDP/TCP, RTDE, latencija)**.
4. **Eksperimentalni postav** — hardver (OptiTrack, URSim/UR3e, mreža); sudionici (ako ih
   ima); **sigurnosni protokoli** (rate limit, range limit, fail-safe, e-stop — §D.2).
5. **Rezultati i analiza** — metrike; grafovi; greške, **latencija/jitter**, robusnost
   (gubitak paketa, nagle promjene).
6. **Rasprava (Discussion)** — ograničenja; **usporedba s literaturom** (svaki rad iz §E
   stvarno upotrijebljen u usporedbi s vlastitim rješenjem).
7. **Zaključak i budući rad**.

> Strogo paziti na limit od **12 stranica** — `build-docs` upozorava ako je premašen
> (`max_pages: 12`). Kod/konfiguracija idu sažeto u tekst + repo (`src/`), ne kao dump.

Build: `.ai/scripts/helpers/build-docs.ps1 -Version v1.0` → `dist/v1.0/main.pdf`.

---

## G. Tijek rada i pravila projekta

- **Orkestracija** (delegiraj specijalistima, ne radi sam): `latex_architect` (setup docs,
  jednom) → `data_fetcher` (literatura) → `writer` (poglavlja) → `qa_reviewer` (pregled) →
  `latex_surgeon` (ako kompilacija pada) → `rag_indexer` (ingest novih PDF-ova).
- **Proaktivni git**: nakon svake logičke cjeline `checkpoint.ps1 "feat: opis"`. Stop hook
  traži čist `git status`.
- **Podaci**: `data/raw/` read-only (hook blokira pisanje); obrađeno u
  `data/processed/<izvor_ddmmyyyy_hhmmss>/`. OptiTrack snimke iz vježbi kopirati u
  `data/raw/` (ili referencirati izvornu lokaciju) i obrađivati u `data/processed/`.
- **Točnost**: činjenice i citati kroz `rag query`, nikad iz memorije.
- **Jezik**: chat hrvatski; kod, komentari, commit poruke, README engleski.
- **Token ekonomija**: ciljano pretraživanje, sažimaj napredak u `STATE.md` svakih ~5 koraka.

---

## H. Checklist predaje

- [ ] `project.yaml`: profesor (titula + ime) dopunjen umjesto placeholdera.
- [ ] Sva 4 obavezna polja popunjena (`author_name`, `course_name`, `seminar_title`, `professor_name`).
- [ ] PDF **≤ 12 stranica** (znanstveni rad).
- [ ] Struktura znanstvenog rada poštovana (Abstract → … → Zaključak i budući rad, §F).
- [ ] **≥ 5 znanstvenih radova**, svi **≥ 2021**, izvori IEEE/Springer/Elsevier/ACM.
- [ ] Literatura **korištena** (odabir metode **i** usporedba), ne samo citirana.
- [ ] Svi citati dolaze iz `rag query` (nema izmišljenih ključeva).
- [ ] Implementacija + evaluacija dovršene; kod i koraci za postavljanje dokumentirani.
- [ ] **Demonstracija praktičnog dijela** pripremljena (live u laboratoriju).
- [ ] `qa_reviewer` prošao (`docs/REVIEW.md` bez blokirajućih nalaza).
- [ ] Build čist → `dist/v1.0/main.pdf`.
- [ ] Predano **3 dana prije** prijavljenog ispitnog roka.
- [ ] `git status --porcelain` prazan.
```
