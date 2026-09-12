# 03 — PRIKUPLJANJE PODATAKA (što, kako, kamo)

Cilj: izaći iz labosa sa **svim** podacima za rad, uredno imenovanima, bez naknadnog "ajoj nemam".

## Kamo sve ide
- Mjerni podaci (auto): `data/raw/lab_session_01092026_020000/telemetry/<ID>.csv` + `<ID>.summary.json` (preko `--latency-csv`).
- Snimke ekrana/videa: `data/raw/lab_session_01092026_020000/camera/<ID>_<opis>.mp4`
- Fotografije postava/robota: `data/raw/lab_session_01092026_020000/camera/<ID>_<opis>.jpg`
- Živa OptiTrack snimka: `data/optitrack/live/<naziv>.csv` (Motive export)
- Offline benchmark izlazi: `data/processed/` (graf + ispis)

## Konvencija imenovanja
`<FAZA-ID>_<kratki-opis>` — npr. `P1-02_no_filter`, `P2-05_step`, `P2-08_estop`.
Isti `ID` koristi u `run_log.csv`, CSV-u i media datotekama → lako se poveže.

## Što snimiti po tipu testa
| Test | Mjerno (auto) | Snimka ekrana | Foto | Bilješke |
|---|---|---|---|---|
| Latencija/filtri (P1-01..04, P2-01..04) | ✅ CSV+json | poželjno (robot+graf) | — | filter, take, dojam glatkoće |
| Gubitak paketa (P1-05/06) | ✅ | — | — | `rx_loss_pct`, stabilnost |
| Rate-limit / nagli pokret (P1-07, P2-05) | ✅ | ✅ **obavezno** | — | je li robot vidljivo ograničen |
| Range-limit (P2-06) | ✅ | ✅ obavezno | — | staje li na granici |
| Fail-safe (P1-08, P2-07) | ✅ | ✅ obavezno | — | vrijeme do zaustavljanja, ponašanje |
| E-stop (P2-08) | ✅ | ✅ obavezno | ✅ | reakcija, oporavak |
| pHRI (P2-09) | upitnik | poželjno | — | `phri_questionnaire.md` |
| Postav (jednom) | — | — | ✅ **obavezno** | OptiTrack, robot, markeri na ruci |

## Mapiranje na sekcije rada (znanstveni rad, max 12 str.)
| Sekcija rada | Iz čega |
|---|---|
| Eksperimentalni postav | foto postava, IP/mreža tablica (01_SETUP), sigurnosne granice |
| Rezultati i analiza | `summary.json` (latencija/jitter/gubitak), graf benchmarka, snimke |
| Metodologija (filtri/komunikacija) | usporedba filtara P*-01..04 + offline benchmark |
| Rasprava (pHRI, sigurnost) | `phri_questionnaire`, fail-safe/e-stop snimke, usporedba s literaturom |
| Sigurnosni protokoli | `safety_signoff.md`, granice, e-stop/fail-safe rezultati |

## Latencija — VAŽNO za točnost
- Latencija (`summary.json`) je valjana kad su **sender (bridge) i pipeline na ISTOM računalu**
  (wall-clock je usporediv). 
- Ako su na **različitim računalima** → satovi nisu sinkronizirani; apsolutna latencija je
  pomaknuta za offset. Tada: ili pokreni bridge i pipeline na istom računalu, ili sinkroniziraj
  satove (NTP), ili tu vrijednost tretiraj kao relativnu (usporedbe između runova ostaju valjane).
- **Jitter i gubitak paketa su valjani neovisno o satovima.**

## Na kraju sesije (5 min)
- [ ] Prekopiraj/uvjeri se da su svi `data/raw/lab_session_01092026_020000/telemetry/*` i `data/optitrack/live/*` spremljeni.
- [ ] Ispunjen `run_log.csv` (svi ID-evi), `results_tables.md`, `safety_signoff.md`.
- [ ] `git add` + commit (`checkpoint.ps1 "data: 🤖 [AI] lab rezultati <datum>"`).
