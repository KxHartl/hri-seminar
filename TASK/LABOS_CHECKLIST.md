# Spremnost za labos — checklist

> Ažurirano nakon lab sesija 26.–27. 6. 2026. i pripreme za novi odlazak.
> Operativni protokol nove sesije: **`testing/lab/protocols/08_session_plan.md`**.

## ✅ Potvrđeno na stvarnom hardveru

| Provjera | Rezultat |
|---|---|
| Jedinični testovi | **66/66** zelena (`pytest src/tests`) |
| Robot **UR3e**, PolyScope 5.9.5, `192.168.40.50` | RTDE receive + servoJ rade (**traži Remote Control mod**) |
| Motive 3.0.1 / NatNet 4.0, `192.168.40.31` | **unicast** 120 Hz (multicast = 0 okvira) |
| Segmenti: `nadlaktica`=18, `podlaktica`=17, `saka`=16 | ≥3 markera po segmentu, čitani preko NatNet SDK-a |
| 1-DOF: kut lakta → **J3** | živo potvrđeno (URSim) |
| 6-DOF mimikrija → J1–J6 | živo na UR3: 119,9 Hz, 0 % gubitka, median 4,5 ms |
| Fail-safe pri gubitku signala | radi (URSim); **na robotu još neizmjereno** |

## ⚠️ Ispravci u odnosu na stariju verziju ovog dokumenta

- **2026-08-31: robot je zamijenjen.** Sada je **UR3e (e-Series)**, PolyScope 5.9.5,
  na `192.168.40.50` — a ne UR3/CB3 3.12 na `.27` kao u lipanjskoj sesiji. Zato
  **treba „Remote Control" mod** (na CB3 ga nije bilo): ☰ → Settings → System →
  Remote Control → Enable, pa gornji desni prekidač → *Remote*. Uz to i dalje
  vrijedi: mode 7 (RUNNING) + safety NORMAL.
- Izvor više nisu 4 markera šake (`zapesce/palac/srednji/mali`), nego **3 kruta tijela**
  (segmenti ruke). Živi izvor ide preko **NatNet SDK-a** (`--sdk` / `--arm`), jer naš
  parser ne čita NatNet 4.0 definiciju modela.
- Samo **jedan** NIC smije biti na `192.168.40.0/24` — inače Windows rutira promet na
  krivi kabel i robot izgleda nedostupno.

## ❌ Što je i dalje OTVORENO (svrha nove sesije)

| Otvoreno | Test u `09_PLAN_SESIJE.md` |
|---|---|
| **Vjernost praćenja** — dosad se nije logirao nijedan kut | T-01…T-03 |
| Usporedba filtara na **stvarnom** signalu lakta | T-04…T-07 |
| **Sigurnosni slojevi izmjereni** (rate-limit, range-limit, fail-safe, e-stop) | T-08…T-12 |
| Utjecaj kašnjenja na upravljanje (objektivno) | T-13 |
| Kontrolirani gubitak paketa | T-14…T-18 |
| Kontinuirani rad (najdulji dosad: 27 s) | T-19 |
| Nagli pokret na robotu (dosad samo sintetički) | T-20 |
| Fotografija postava + videi sigurnosnih testova | B0 / B4 |
| Eskalacija granica potpisana u `safety_signoff.md` | B0 |

## Sigurnost (OBAVEZNO)

- Prvi pokreti **bez čovjeka u radnom prostoru**.
- **Hardverski e-stop na dohvat i testiran** prije svakog runa.
- Kreni konzervativno (`--max-speed-dps 12–15`, `--range-dps 15–20`), pa postupno otpuštaj
  i svaki korak upiši u `testing/lab/templates/safety_signoff.md`.
- Provjeri smjer gibanja na malom pokretu prije punog raspona (`--invert` ako treba).

## Mjerenje latencije — valjanost

`t_capture` je wall-clock, pa je latencija valjana **samo ako su most i pipeline na istom
računalu**. Ako nisu — sinkroniziraj satove (NTP) ili tretiraj brojku kao relativnu.
**Jitter i gubitak paketa valjani su neovisno o satovima.**

## Verdikt

Kod je spreman: pipeline sada logira kutove, stvarni kut robota i događaje sigurnosnog
sloja, te podržava injektiranu latenciju i dokazni softverski e-stop. Ostaje **prikupiti
podatke** po protokolu `testing/lab/protocols/08_session_plan.md`.
