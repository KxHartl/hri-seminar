# testing/lab — vodič za testiranje u laboratoriju

Sve što treba da u labosu brzo, profesionalno i točno provedeš sva testiranja i prikupiš
podatke za seminar (znanstveni rad). Čitaj redom; u labosu drži otvoren `CHEATSHEET.md`.

## ⚠️ SIGURNOST PRIJE SVEGA
- **Prvi pokreti uvijek bez čovjeka u radnom prostoru robota.**
- **Hardverski e-stop na dohvat ruke i testiran prije svakog runa.**
- Kreni s **konzervativnim granicama** (`config.safety`: 20 °/s, ±30°), pa postupno otpuštaj.
- Snimke imaju velik raspon fleksije (do ~95°) → robot J4 se stvarno i brzo giba.

> **Ovo je stara struktura (2 faze, robot UR3e, markeri šake).** Za novi odlazak
> koristi **`09_PLAN_SESIJE.md`**: sustav sada logira i kutove (`--track-csv`) i
> stvarni kut robota (`--log-actual`), pa se mjeri vjernost praćenja, a ne samo
> latencija. Robot je od 2026-08-31 **UR3e** (`192.168.40.50`, traži *Remote Control*;
> ranije UR3/CB3 na `.27`), izvor su **3 kruta tijela** (segmenti ruke).

## Redoslijed (dvije faze)
1. **Faza 1 — spremljeni podaci + stvarni UR3e** (replay → robot). Sve je već verificirano u
   simulaciji; mijenja se samo odredište. Cilj: potvrditi robota + prikupiti latenciju/
   robusnost/sigurnost na stvarnom hardveru.
2. **Faza 2 — živi OptiTrack + UR3e** (Motive → bridge → robot). Cilj: živa interakcija,
   pHRI mjerenja, sudden-movement i fail-safe na živom streamu.

## Datoteke u ovom folderu
| Datoteka | Svrha |
|---|---|
| `00_PREFLIGHT.md` | Što ponijeti/pripremiti i potvrditi PRIJE labosa (checkbox) |
| `01_SETUP.md` | Korak-po-korak postavljanje u labosu (robot, mreža, Motive) |
| `02_TEST_PROTOCOL.md` | *(zastarjelo)* stara matrica `P1-*/P2-*` — zamijenjena s `09_` |
| `03_DATA_COLLECTION.md` | Što snimiti/spremiti, imenovanje, mapiranje na sekcije rada |
| `04_TROUBLESHOOTING.md` | Brza rješenja čestih problema |
| `09_PLAN_SESIJE.md` | **PROTOKOL NOVE SESIJE (T-01…T-21)** — ovo nosiš u labos |
| `10_MOTIVE_SETUP.md` | **Motive**: streaming + kruta tijela (ID 25/24/16), kalibracija `arm_axes` |
| `run_scripts/` | **Skripte koje pokrećeš u labosu** (provjera, home, slobodno gibanje, hod po zglobovima) |
| `CHEATSHEET.md` | **Jednostranična** copy-paste šalabahter (drži otvoreno) |
| `templates/run_log.csv` | Dnevnik svih runova (popunjavaj u hodu) |
| `templates/results_tables.md` | Tablice rezultata za rad (popunjavaj) |
| `templates/safety_signoff.md` | Sigurnosni checklist po sesiji (potpiši) |
| `templates/phri_questionnaire.md` | *(neaktivno)* upitnik — nema studije s više ispitanika |
| `results/` | **Ovamo idu svi prikupljeni podaci** (CSV, summary, slike, snimke) |

## Brzi pregled — što prikupljamo (za rad)
- **Latencija/jitter** (auto: CSV + `.summary.json` po runu) → sekcije Rezultati, Rasprava.
- **Usporedba filtara** (One-Euro vs Butterworth vs EMA vs none) → Metodologija, Rezultati.
- **Robusnost** (gubitak paketa 0/10/30%, fail-safe, e-stop) → Rezultati, Sigurnost.
- **Osjetljivost na nagle pokrete** (step/flick test) → Rezultati.
- **pHRI subjektivno** (osjećaj kontrole pri raznim postavkama) → Rasprava.
- **Snimke/slike** (robot + graf, postav) → figure u radu.
- **Živa OptiTrack snimka** (Motive export CSV) → offline benchmark (`src.tools.benchmark`).

> Cilj latencije iz literature: **< ~100 ms**. U simulaciji smo imali median ~4 ms — u labosu
> očekuj nešto više zbog stvarne mreže/robota; svejedno bi trebalo biti dobro ispod 100 ms.
