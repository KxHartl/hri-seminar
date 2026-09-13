# REVIEW — pregled prije predaje

**Datum:** 2026-09-13 · **Verzija rada:** `dist/v1.5/main.pdf`, 12/12 stranica
**Prethodna recenzija (2026-06-29) je poništena** — rad je od tada napisan iznova
oko šesterostupanjske lab sesije, pa se njezini nalazi više ne odnose ni na jedan
postojeći odlomak.

---

## 1. Ispravci u analizi koji su prethodili pisanju

Revizija prije pisanja pronašla je da su agregirane tablice iz commita `11c4b4a`
mjerile nešto drugo od onoga što tvrde. Sve je popravljeno prije nego što je
ijedna brojka ušla u tekst.

| # | Nalaz | Status |
|---|---|---|
| N1 | Tablice su uzimale `command_to_actual` — koliko robot slijedi vlastitu naredbu, ne ruku | Riješeno: uveden `scaled_input_to_actual` (ulaz × gain·invert vs stvarni kut) i `target_to_actual` |
| N2 | Lag 112,4 ms u svakom retku svake tablice | Objašnjeno: to je `servoj.lookahead_time`; sada je izdvojen kao zadnji stupanj u tablici razlaganja |
| N3 | `_estimate_lag_ms` saturirao na 60 uzoraka → konstantnih 481,5 ms | Riješeno: prozor u sekundama, predznakom-korigirana korelacija, `NaN` na rubu prozora, tri testa |
| N4 | RMSE računat bez kompenzacije faznog pomaka | Riješeno: uz `rmse_deg` se izvještava i `rmse_aligned_deg` |
| N5 | Ulaz zapisan prije pojačanja, izlaz poslije → negativne korelacije | Riješeno: ulaz se skalira konfiguriranim `arm_mapping` prije usporedbe |
| N6 | 41–75 % taktova bez nove vrijednosti kanala tiho ulazilo u RMSE kao nule | Riješeno: `_hold_mask` ih prepoznaje, `_fill_holds` ih drži kao što ih drži i pipeline; efektivna frekvencija ulaza sada je izvještajna veličina |
| N7 | Parametri filtara u tablici (4,0 Hz, α=0,15) proturječili konfiguraciji (6,0 Hz, α=0,2) | Riješeno: čitaju se iz `src/config/default.yaml` |
| N8 | Slomljen `\textit` (doslovni tab) u `safety_summary.tex` | Riješeno; provjera `grep -P "\t"` nad `docs/tables/` prazna |
| N9 | Tablica sigurnosnih slojeva bila hardkodirana | Riješeno: brojači se čitaju iz `*.track.summary.json` |
| N10 | `rx_rate_hz ≈ 500`, `rx_reordered ≈ 66 %`, `T-13d rx_lost = 2 536 801` | Nije popravljivo iz zapisa; te se statistike **ne citiraju** u radu, a pojava je opisana u §4.2 i u Ograničenjima |
| N11 | „End-to-end latencija" nije uključivala optički put ni mrežu | Riješeno: u radu se dosljedno zove *latencija obrade*, uz eksplicitnu ogradu |
| N12 | T-10 ima `halted_ticks = 0` iako je test fail-safea | Nije greška nego ponašanje mosta; opisano u §4.7 kao nalaz, ne prešućeno |
| N13 | `--drop-rate` uz `--external` tiho bez učinka | Riješeno: pipeline sada upozorava; blok gubitka opisan kao offline model |
| N14 | Pet runova gubitka snimljeno je pet različitih pokreta | Riješeno: `sweep_from_base` primjenjuje sve stope na istu snimku |

## 2. Provjera brojki u tekstu

Svaka numerička tvrdnja provjerena je protiv `data/raw/lab_session_01092026_020000/telemetry/run_log.csv` i
pripadnih `*.summary.json`. Nalazi i ispravci:

| Tvrdnja | Izvor | Ishod |
|---|---|---|
| takt 123,9–124,7 Hz | `run_log.csv`, 17 runova izvan sweepa | ispravljeno iz „124,6 Hz kroz sve pokuse" |
| medijan latencije 3,0–4,0 ms | isto | točno |
| p99 8,7–10,5 ms u runovima praćenja, 14,8 ms u runu s e-stopom | isto | ispravljeno; izlet je sada imenovan |
| efektivna frekvencija ulaza 31–73 Hz | `*.track.summary.json` → `input_update_rate_hz` | točno (30,9–73,3) |
| RMSE$_\text{p}$ 0,36–3,00°, $r$ 0,68–0,95 (T-02) | `T-02.track.summary.json` | točno |
| RMSE$_\text{p}$ 0,49–6,24°, $\tau$ 241–787 ms (T-03) | `T-03.track.summary.json` | točno |
| razlaganje 385 / 185 / 112 ms | `T-02.track.summary.json` | točno; 73 ms i 200 ms su razlike |
| filtri 1,00–2,79°, 217–682 ms, 621–1235 taktova | `T-04…T-07` | točno |
| One-Euro 56,6 % jittera, 50–100 ms; Butterworth i EMA 25–42 ms | `data/processed/benchmarks_02092026/filter_bench.summary.json` | točno |
| sweep 3,1 / 59,3 / 107,4 / 203,2 / 403,9 ms | `T-13a…e.summary.json` | točno |
| p99−p95 < 7 ms u svakoj točki sweepa | isto | točno (1,3–4,7 ms) |
| sigurnost 23,8 % / 13,0 % / 50,1 % | `T-08`, `T-09`, `T-12a` | točno |
| gubitak: starost 7,5→19,7 ms, RMSE 4,95→6,92° | `loss_sweep/L-*.json` | točno |
| osjetljivost 0,77–1,40°/mm | `filter_bench.summary.json` | točno |
| 80 testova | `pytest src/tests -q` | točno |
| ukupno gibanje „nešto više od deset minuta" | zbroj trajanja = 620 s | ispravljeno iz „oko jedanaest minuta" |
| prijelaz vođenja na 100 ms | `testing/lab/protocols/10_subjective_evaluation.md` | ispravljeno: kontinuirano do 50 ms, čekanje na 100 ms |
| „stotinjak puta" (385 ms / 3 ms) | izračun | ispravljeno iz „dvjesto puta" |
| 21 run s telemetrijom + 1 samo video + 3 neizvedena | `run_log.csv` | ispravljeno iz „24 planirana pokusa" |

## 3. Formalni zahtjevi kolegija

| Zahtjev | Status |
|---|---|
| Znanstveni rad, ≤ 12 stranica | 12 stranica (na limitu) |
| Struktura (sažetak → uvod → metodologija → postav → rezultati → rasprava → zaključak) | ispunjeno |
| ≥ 5 znanstvenih radova, svi ≥ 2021, IEEE/Springer/Elsevier/ACM | 16 ključeva (15 radova + norma ISO/TS 15066), 13 iz kvalificiranih izvora (uz `casiez2012` kao izvorni rad o One-Euro filtru i `zhu2022` kao potporni) |
| Literatura korištena, ne samo citirana | svaki ključ pojavljuje se u obrazloženju metode ili u usporedbi s vlastitim rješenjem |
| Nema izmišljenih `\cite` ključeva | provjereno: 16 u `.bib`, 16 citirano, presjek potpun |
| Implementacija + evaluacija | `src/`, 80 testova, 21 laboratorijski run |
| Kolegij naveden na naslovnici | dodan redak *Kolegij: Interakcija čovjeka i robota* (`docs/main.tex`) |
| Demonstracija u laboratoriju | `testing/lab/protocols/07_demo_runbook.md`, video zapisi u `data/processed/video_clips_01092026/camera/` |

## 4. Formatiranje (AGENTS.md §8)

- Bez prelamanja riječi: `\hyphenpenalty=10000`, `\exhyphenpenalty=10000`,
  `\righthyphenmin=62`, `\lefthyphenmin=62` u `docs/main.tex`.
- `\FloatBarrier` na kraju svih šest poglavlja; `placeins` uz `[section]`.
- Jednostupčane tablice pinane s `[H]` pa stoje uz tekst koji ih referencira;
  dvostupčani floatovi (`figure*`, `table*`) koriste `[t]` jer LaTeX za njih ne
  podržava `h`/`H`.
- Build: 1 overfull hbox (5,9 pt), bez „Undefined reference" i bez
  „multiply defined labels".

## 5. Otvoreno prije predaje

1. Mentor se ne imenuje (odluka autora) — polja `professor_*` uklonjena iz
   `project.yaml`; naslovnica rada ih ionako ne ispisuje. Kolegij je od v1.5 naveden.
2. Neizvedeni pokusi (URSim referenca, endurance, ponovljivost) i modelirani
   gubitak paketa navedeni su u Ograničenjima. Ako se otvori termin u
   laboratoriju, prioritet je desetominutni endurance run i ispravno injektiran
   gubitak preko `live_sender --drop-rate`.
3. Izvor prezentacije (`docs/presentation/`) nije u repou — samo izvezeni `.pptx` i
   `.pdf`. Izmjene slajdova su ručne.

> Ispunjeni pHRI upitnik obaju sudionika nalazi se u
> `testing/lab/protocols/10_subjective_evaluation.md` (refaktor `LabTESTING/` →
> `testing/lab/` preimenovao ga je iz `SUBJEKTIVNI_UPITNIK_REZULTATI.md`, pa ga
> starije reference traže pod starim imenom).
