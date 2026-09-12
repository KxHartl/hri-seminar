# 02 — PROTOKOL TESTIRANJA (matrica + komande)

> ⚠️ **ZASTARJELO — zamijenjeno s `09_PLAN_SESIJE.md`.**
> Ova je matrica pisana za UR3e i 4 markera šake, i nikad nije izvedena (samo `P1-00`).
> Runovi po njoj bilježe **samo timing, bez kutova**, pa ne mogu potkrijepiti vjernost
> praćenja. Zadržano radi povijesti i zato što su opisi testova (rate-limit, fail-safe,
> e-stop) i dalje korisni kao pozadina.

Svaki run automatski sprema `data/raw/lab_session_01092026_020000/telemetry/<ID>.csv` + `<ID>.summary.json` (latencija,
gubitak, jitter). **Uz svaki run zapiši redak u `templates/run_log.csv`** i po potrebi snimi
ekran/foto. Trajanje runova: 20–30 s (osim sigurnosnih, kraće).

Konvencija: pokreni iz korijena repozitorija; zamijeni `<UR3e>` stvarnim IP-em.
Bridge (izvor) i pipeline idu u **dva terminala**.

---

## FAZA 1 — spremljeni podaci + UR3e (replay → robot)

Izvor (Terminal A, drži upaljeno cijelu fazu):
```
.venv/Scripts/python -m src.tools.replay_sender --port 51000 \
  --take data/raw/reference_mocap/vjezbe_02/hri_snimanje_vjezbe_02_x.csv
```
Pipeline (Terminal B, jedan po test):
```
.venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink ur3e \
  --seconds 25 --latency-csv data/raw/lab_session_01092026_020000/telemetry/<ID>.csv [--filter <F>] [--drop-rate <D>]
```

| ID | Cilj | Promjena | Očekivano / što gledati |
|----|------|----------|--------------------------|
| **P1-01** | Baseline | `--filter one_euro` | glatko praćenje, median latencija ≪100 ms, 0% gubitka |
| **P1-02** | Bez filtra | `--filter none` | vidljiviji trzaji/šum → usporedi u radu |
| **P1-03** | Butterworth | `--filter butterworth` | glatko, nešto drukčiji lag |
| **P1-04** | EMA | `--filter ema` | glatko, mali lag |
| **P1-05** | Gubitak 10% | `--drop-rate 0.1` | stabilno; `rx_loss_pct ≈ 10` |
| **P1-06** | Gubitak 30% | `--drop-rate 0.3` | i dalje stabilno; veći jitter, bez destabilizacije |
| **P1-07** | Rate-limit (sigurnost) | take `..._x` (raspon 95°), `safety 20 °/s` | robot **ne može pratiti** nagle dijelove → glatko ograničeno (dokaz rate-limita) |
| **P1-08** | Fail-safe (gubitak signala) | **ugasi Terminal A** usred runa | robot **stane/drži** poziciju u < `signal_timeout_s`; bez trzaja |

Snimi ekran za P1-01 i P1-02 (usporedba glatkoće). Za P1-08 snimi trenutak prekida.

---

## FAZA 2 — živi OptiTrack + UR3e (Motive → bridge → robot)

Izvor (Terminal A):
```
.venv/Scripts/python -m src.tools.live_sender --server-ip <Motive> --client-ip <NIC> \
  --port 51000 [--multicast]
```
> Prvo provjeri da bridge prima markere (log) i da pipeline javlja `primljeno > 0`.

Pipeline (Terminal B) — isti oblik kao Faza 1, `--external --port 51000 --sink ur3e`.

| ID | Cilj | Postupak | Očekivano / što gledati |
|----|------|----------|--------------------------|
| **P2-01** | Baseline live | mirno gibaj šaku ±, `one_euro` | robot prati fleksiju glatko |
| **P2-02..04** | Filtri | redom `none/butterworth/ema` | subjektivna i mjerena razlika (vidi pHRI upitnik) |
| **P2-05** | Nagli pokret (step) | brzi "flick" šake gore-dolje | gledaj odziv/overshoot/rate-limit; snimi ekran |
| **P2-06** | Range-limit | namjerno prekorači raspon fleksije | robot **stane na granici** (±range), ne nastavlja |
| **P2-07** | Fail-safe (okluzija) | rukom prekrij markere / izađi iz volumena | robot **drži** poziciju (timeout) → vrati markere → nastavlja |
| **P2-08** | E-stop | tijekom gibanja pritisni **hardverski e-stop** | robot odmah staje; zabilježi reakciju |
| **P2-09** | pHRI subjektivno | 2–3 postavke (npr. one_euro vs none; po želji dodana latencija) | ispuni `templates/phri_questionnaire.md` |

Za P2-05/06/07/08 obavezno **snimka ekrana + robota** (figure + dokaz sigurnosti u radu).

---

## Dodatno: živa OptiTrack snimka za offline analizu
Da dobiješ usporedbu filtara/osjetljivost na **stvarnim živim podacima** (kao u sim benchmarku):
1. U Motive **snimi take** dok mičeš šaku (15–25 s) i **exportaj u CSV** (isti format kao
   postojeće snimke). Spremi u `data/optitrack/live/`.
2. Pokreni offline benchmark na njoj (prilagodi putanju u `src/tools/benchmark.py` ili kopiraj
   take među `vjezbe_02`): generira jitter/lag/osjetljivost + graf u `data/processed/`.

---

## Minimalni set (ako je vrijeme kratko)
P1-01, P1-02, P1-06, P1-08 → pa P2-01, P2-05, P2-07, P2-08, P2-09. To pokriva latenciju,
filtriranje, robusnost, sigurnost i pHRI — dovoljno za sve sekcije rada.
