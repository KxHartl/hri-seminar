# Prijedlog novih testova (review pass 2)

> Svrha: zatvoriti rupe koje postojeći logovi NE mogu pokriti. Ključno ograničenje
> postojećih snimaka: CSV-ovi u `data/raw/lab_session_01092026_020000/telemetry/` sadrže **samo timing**
> (`t_capture, t_command, latency_ms, signal_age_ms`) — **nema zabilježenih kutova**,
> pa se vjernost praćenja (ulaz vs izlaz) i točnost ne mogu izračunati unatrag.
> Svaki test ispod precizira: ŠTO se snima, KAKO, i KOJU tvrdnju u radu potkrepljuje.

## Prioritet 1 — Vjernost praćenja (ulaz vs izlaz)  *(najvažnije)*

- **Cilj:** grafički i brojčano pokazati da robot vjerno prati ruku — središnja
  tvrdnja rada koja trenutno nema figuru ni metriku.
- **Snimanje:** proširiti logging (npr. u `src/pipeline/main.py` ili novi
  `src/tools/track_log.py`) da uz timing bilježi **ulazni kut** (iz OptiTracka,
  prije filtra) i **naredbeni/izmjereni kut robota** (po taktu), za svaki aktivni
  zglob. Format: `t, ulaz_deg, naredba_deg, [po zglobu]`.
- **Protokol:** 30–60 s mješavine sporih i brzih pokreta; na **URSim** i na
  **UR3** (uske granice kao dosad). Po jedan run za svaki način (single-joint i
  6-DOF) — vidi otvoreno pitanje o DOF-u dolje.
- **Izlaz:** (a) overlay-figura ulaz vs naredba kroz vrijeme; (b) **RMSE** i
  **lag** (kros-korelacija ulaz→izlaz) u summary JSON; (c) opcijski faza vs
  amplituda.
- **Potkrepljuje:** §4 (nedostaje metrika vjernosti), §5.1 ("vjernost" kao ono što
  je bitno).

## Prioritet 2 — Benchmark filtra → perzistirani JSON

- **Cilj:** dati izvor brojkama "56 % manje jittera" i "≈33 ms lag" (sada samo u
  `filter_comparison.png`, bez summary fajla — slabija provenijencija od ostalih).
- **Snimanje:** isti zapis kuta iz Prioriteta 1; pustiti kroz One-Euro /
  Butterworth (6 Hz) / EMA (α=0,2) i zapisati % redukcije jittera + lag [ms] po
  filtru u `data/processed/benchmarks_02092026/filter_bench.summary.json`.
- **Potkrepljuje:** §2.3, §4.2.

## Prioritet 3 — Kontrolirani inducirani gubitak

- **Cilj:** namjerni (ne slučajni) dokaz robusnosti na gubitak. Postojeći dokazi
  su nehotični: GIL in-process (19,9 %) i pogrešna konfiguracija s dvostrukim
  senderom (38 %). Treba ponovljiv, stupnjevan test.
- **Snimanje:** `source.drop_rate` u `src/config/default.yaml` već postoji —
  pokrenuti čisti 120 Hz put uz `drop_rate` = 0,05 / 0,10 / 0,20 i bilježiti
  utjecaj na kut i stabilnost (uz zapis kuta iz Prioriteta 1).
- **Izlaz:** tablica gubitak→RMSE/odstupanje; potvrda da detekcija prijavljuje
  točan postotak.
- **Potkrepljuje:** §4.3 (robusnost), §3.2 (fail-safe).

## Prioritet 4 — Izdržljivost (endurance)

- **Cilj:** p99 i repovi na duljem horizontu; provjera da nema drifta/zastoja.
  Motivacija: runovi `ursim-arm-6dof-v2/v3` imaju **p95 > 1 s, max ~2,7 s** repove
  (v2 ima čist mrežni rx_jitter 1,23 ms → zastoj je na **command/RTDE strani**),
  pa treba potvrditi da na čistom putu dulji rad ostaje stabilan.
- **Snimanje:** 5–10 min kontinuiranog rada na UR3, isti timing logging.
- **Izlaz:** p99/max kroz vrijeme; histogram bez teških repova.

## Prioritet 5 — Per-stage latencija  *(opcijski)*

- **Cilj:** razložiti end-to-end (prijem / izračun / filtar / slanje). §2.5 spominje
  proračun, ali ga rad ne prikazuje.
- **Snimanje:** timestamp po fazi u petlji (mjerači već postoje — proširiti zapis).

## Prioritet 6 — High-res tajmer (dijagnostika)  *(opcijski)*

- **Opažanje:** `rx_jitter_ms` (std neobrađenih međudolaznih vremena) ≈ 32 ms u
  gotovo svim runovima, dok je čisti std (bez praznina/duplikata) ≈ 1,5 ms
  (`interarrival_hist.png`). Iznimka: `ursim-arm-6dof-v2` = 1,23 ms.
- **Provjera:** je li ~32 ms posljedica duplih dolazaka/nakupina i/ili Windows
  granularnosti tajmera (`timeBeginPeriod(1)`). v2 sugerira da se uz bolji tajmer
  rasipanje smanjuje. Nije blokirajuće za rad, ali objašnjava metriku.

---

## ✓ Riješeno: DOF i imenovanje zglobova (odluka korisnika)

- **Obvezni dio = lakat čovjeka → lakat robota (J3)**, anatomski podudarno;
  detaljno objašnjeno u radu §2.4 (afina transformacija, $k\!\approx\!1$).
- Zatim **pregled 6-DOF mimikrije** (svih 6 kanala jedan-na-jedan na J1–J6).
- **J-numeracija usvojena 1-bazirano: J1 baza, J2 rame, J3 lakat, J4–J6 zapešće**
  (definirano jednom u §2.4). Napomena: kod (`arm_pose.py`, `default.yaml`)
  interno koristi 0-bazirane indekse — pri budućim izmjenama paziti na pretvorbu.
- Namjenski single-joint run za vjernost (RMSE/lag) i dalje je koristan (Prioritet 1).
