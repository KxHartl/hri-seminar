# Tablice rezultata (popunjavaj iz `*.summary.json`)

> Vrijednosti se ispišu na kraju svakog runa i spreme u `data/raw/lab_session_01092026_020000/telemetry/<ID>.summary.json`.

## 1. Latencija i jitter po postavci (Faza 1, replay + UR3e)
| ID | filter | median [ms] | p95 [ms] | max [ms] | jitter [ms] | rx rate [Hz] | gubitak [%] |
|----|--------|-------------|----------|----------|-------------|--------------|-------------|
| P1-01 | one_euro |  |  |  |  |  |  |
| P1-02 | none |  |  |  |  |  |  |
| P1-03 | butterworth |  |  |  |  |  |  |
| P1-04 | ema |  |  |  |  |  |  |

## 2. Robusnost na gubitak paketa (Faza 1)
| ID | drop traženo [%] | rx_loss izmjereno [%] | median [ms] | jitter [ms] | stabilno? (D/N) |
|----|------------------|------------------------|-------------|-------------|------------------|
| P1-01 | 0 |  |  |  |  |
| P1-05 | 10 |  |  |  |  |
| P1-06 | 30 |  |  |  |  |

## 3. Sigurnosni mehanizmi
| Mehanizam | Test ID | Rezultat (opis) | Vrijeme reakcije | OK? |
|-----------|---------|------------------|------------------|-----|
| Rate-limit (max brzina J4) | P1-07 |  |  |  |
| Fail-safe (gubitak signala) | P1-08 / P2-07 |  | < signal_timeout_s? |  |
| Range-limit (radni raspon) | P2-06 |  | — |  |
| E-stop | P2-08 |  |  |  |

## 4. Živa interakcija (Faza 2)
| ID | postavka | median [ms] | jitter [ms] | gubitak [%] | dojam (kratko) |
|----|----------|-------------|-------------|-------------|-----------------|
| P2-01 | one_euro |  |  |  |  |
| P2-02 | none |  |  |  |  |
| P2-05 | nagli flick |  |  |  | overshoot? |

## 5. Offline benchmark na živoj snimci (`src.tools.benchmark`)
| filtar | jitter↓ [%] | lag [ms] | RMS vs raw [°] |
|--------|-------------|----------|-----------------|
| one_euro |  |  |  |
| butterworth |  |  |  |
| ema |  |  |  |
| savgol (offline ref) |  | ~0 |  |

Osjetljivost na šum markera: 0.5 mm → ____°, 1.0 mm → ____°, 2.0 mm → ____° (RMS).
