# 00 — PREFLIGHT (prije odlaska u labos)

> **Automatizirano:** `python -m src.tools.preflight` provjerava venv, NatNet SDK,
> config/kalibraciju, put za logiranje kutova i lab-dokumente te vraća grešku ako
> nešto nedostaje. Ova lista pokriva ono što skripta ne može (kabel, kamera, OBS).

Odradi ovo kod kuće/prije termina da u labosu ne gubiš vrijeme.

## Oprema / pristup
- [ ] Laptop s repozitorijem (`hri-seminar`) i radnim `.venv` (Python 3.10, `ur_rtde` instaliran).
- [ ] Provjeri okruženje: ``.venv/Scripts/python -m pytest src/tests -q`` → **34 passed**.
- [ ] Mrežni kabel / pristup labosLAN-u (robot i Motive su na mreži).
- [ ] Telefon/kamera za snimke i fotografije (figure u radu).
- [ ] Alat za snimanje ekrana (OBS / ugrađeni Win+G) — za robot+graf snimke.
- [ ] Ispisan ili otvoren `CHEATSHEET.md` i `templates/run_log.csv`.

## Informacije koje moraš saznati u labosu (zapiši u `01_SETUP.md`)
- [ ] **IP stvarnog UR3e** robota.
- [ ] **IP Motive računala** (NatNet server) + **lokalni NIC IP** laptopa.
- [ ] **NatNet verzija** Motivea; **unicast ili multicast** (+ multicast grupa/portovi ako nestandardno).
- [ ] **Imena markera** u Motive marker setu (moraju sadržavati `zapesce`, `srednji`, `mali`; `palac` opcionalno).
- [ ] Jesu li robot i Motive na **istom računalu kao pipeline**? (bitno za mjerenje latencije — vidi 03).

## Priprema configa (možeš unaprijed)
- [ ] U `src/config/default.yaml` postavi **konzervativne** sigurnosne granice za prvi dan:
      `safety.max_joint_speed_dps: 20`, `safety.joint_range_dps: 30`.
- [ ] Pripremi lab config kopiju ako želiš (npr. `src/config/lab.yaml`) s `robot.sink: ur3e`
      i `robot.ip: <UR3e>` (popuniš na licu mjesta). Ili koristi CLI override `--sink ur3e`.
- [ ] Provjeri `source.live.marker_name_map` (default je identitet na naša imena).

## Provjera koda (offline, bez hardvera)
- [ ] `--mock` živi put radi: pokreni dva terminala (vidi CHEATSHEET, sekcija MOCK) i potvrdi
      da pipeline prima frameove (`primljeno > 0`, `izgubljeno 0%`).
- [ ] `src.tools.check_ursim --no-move` (ako ti je URSim pri ruci) — podsjetnik kako izgleda OK veza.

## Mentalni model (da ne lutaš)
```
Faza 1:  replay_sender (snimka)  ──UDP──►  pipeline --external --sink ur3e  ──RTDE──► UR3e
Faza 2:  Motive ──NatNet──► live_sender ──UDP──► pipeline --external --sink ur3e ──RTDE──► UR3e
```
Pipeline je isti; mijenja se samo izvor i `--sink ur3e` + IP.
