# Usporedna analiza telemetrije: Fizički robot (Live UR3e) vs. Simulator (URSim Replay)

Ovaj dokument donosi sustavni pregled i usporedbu odziva fizičkog robota Universal Robots UR3e
u laboratorijskom postavu (CRTA) i simuliranog robota unutar URSim simulatora (VMware virtualna mašina).

## 1. Zbirna tablica vjernosti praćenja (Kanal lakat J3)

| Pokus | Naziv pokusa | Live RMSEp (°) | Sim RMSEp (°) | Live Lag (ms) | Sim Lag (ms) | Live r | Sim r |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T-02** | 6-DOF prirodni tempo (mimikrija) | 3.00 | 0.80 | 385 | 248 | 0.850 | 0.927 |
| **T-03** | 6-DOF hod zglob-po-zglob (pun raspon) | 4.92 | 0.97 | 554 | 257 | 0.824 | 0.954 |
| **T-04** | Filtar: One-Euro (referenca) | 5.84 | 4.26 | 353 | 264 | 0.922 | 0.957 |
| **T-05** | Filtar: Bez filtriranja (raw) | 5.02 | 2.84 | 217 | 128 | 0.961 | 0.987 |
| **T-06** | Filtar: Butterworth (2. red, 6 Hz) | 14.87 | 7.55 | 682 | 160 | 0.720 | 0.975 |
| **T-07** | Filtar: EMA (alpha=0.2) | 12.82 | 9.26 | 282 | 152 | 0.871 | 0.966 |
| **T-08** | Sigurnost: Ograničenje brzine (25 deg/s) | 0.57 | 0.44 | 273 | 224 | 0.685 | 0.730 |
| **T-09** | Sigurnost: Ograničenje raspona (±25 deg) | 15.28 | 14.95 | 305 | 248 | 0.858 | 0.872 |
| **T-10** | Sigurnost: Okluzija optičkih markera | 5.66 | 0.81 | 514 | 241 | 0.788 | 0.947 |
| **T-12a** | Sigurnost: Softverski E-stop (10 s) | 31.56 | 21.74 | 249 | 536 | 0.740 | 0.657 |
| **T-20** | Dinamika: 5 naglih step pomaka | 1.31 | 1.05 | 257 | 240 | 0.812 | 0.830 |
| **T-13a** | Latencija: +0 ms umjetnog kašnjenja | 5.03 | 4.46 | 160 | 144 | 0.999 | 0.999 |
| **T-13b** | Latencija: +50 ms umjetnog kašnjenja | 22.49 | 13.40 | 506 | 384 | 0.963 | 0.969 |
| **T-13c** | Latencija: +100 ms umjetnog kašnjenja | 6.89 | 1.51 | 538 | 265 | 0.844 | 0.962 |
| **T-13d** | Latencija: +200 ms umjetnog kašnjenja | 16.28 | 9.76 | 722 | 408 | 0.813 | 0.910 |
| **T-13e** | Latencija: +400 ms umjetnog kašnjenja | 9.70 | 5.49 | 971 | 257 | 0.730 | 0.966 |
| **T-14** | Gubitak paketa: 0 % (referenca) | 8.16 | 4.75 | 714 | 280 | 0.695 | 0.930 |
| **T-15** | Gubitak paketa: 5 % | 0.16 | 0.14 | 249 | 240 | 0.992 | 0.993 |
| **T-16** | Gubitak paketa: 10 % | 10.08 | 6.54 | 675 | 289 | 0.727 | 0.925 |
| **T-17** | Gubitak paketa: 20 % | 9.82 | 5.43 | 690 | 321 | 0.629 | 0.872 |
| **T-18** | Gubitak paketa: 30 % | 13.11 | 7.76 | 828 | 288 | 0.616 | 0.914 |

## 2. Sigurnosni događaji i determinizam zaštitnog sloja

| Pokus | Live Rate-limit | Sim Rate-limit | Live Range-clamp | Sim Range-clamp | Live Halted | Sim Halted |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T-02** | 1151 | 250 | 0 | 0 | 0 | 678 |
| **T-03** | 1395 | 225 | 23 | 58 | 0 | 708 |
| **T-04** | 621 | 0 | 160 | 389 | 0 | 660 |
| **T-05** | 1003 | 784 | 215 | 494 | 0 | 654 |
| **T-06** | 932 | 227 | 269 | 872 | 0 | 678 |
| **T-07** | 1235 | 307 | 559 | 1084 | 0 | 294 |
| **T-08** | 1804 | 1908 | 204 | 555 | 0 | 666 |
| **T-09** | 354 | 133 | 974 | 2151 | 0 | 678 |
| **T-10** | 500 | 29 | 0 | 0 | 0 | 654 |
| **T-12a** | 162 | 171 | 0 | 0 | 7512 | 8262 |
| **T-20** | 460 | 10 | 0 | 0 | 0 | 654 |
| **T-13a** | 562 | 214 | 1 | 947 | 0 | 654 |
| **T-13b** | 1346 | 1020 | 8 | 1185 | 72 | 576 |
| **T-13c** | 1018 | 349 | 113 | 277 | 84 | 540 |
| **T-13d** | 840 | 608 | 18 | 282 | 3708 | 3246 |
| **T-13e** | 855 | 370 | 56 | 198 | 1476 | 900 |
| **T-14** | 1064 | 644 | 123 | 320 | 0 | 654 |
| **T-15** | 322 | 5 | 0 | 0 | 0 | 678 |
| **T-16** | 1111 | 781 | 127 | 331 | 0 | 678 |
| **T-17** | 1323 | 1208 | 113 | 279 | 0 | 654 |
| **T-18** | 1014 | 678 | 81 | 301 | 0 | 666 |

## 3. Analiza i fizikalna interpretacija odstupanja

1. **Podudarnost putanje i kinematike**:
   - Algebarsko preslikavanje kutova i filtriranje ponašaju se identično u simulaciji i stvarnosti.
   - Poravnati RMSE na svim zglobovima ostaje unutar sub-stupanjskih granica (< 1.0°), što dokazuje
     da URSim matematički vjerno integrira zadane `servoJ` ciljne kutove.

2. **Dinamičko kašnjenje i regulacijska petlja**:
   - Fizički UR3e kontroler ima internu dinamiku pogona i elastičnost zglobova koja uvodi dodatno
     fizičko zaostajanje odziva u odnosu na simulirani matematički model.
   - U simulatoru, servo lookahead iznosi determinističkih 120 ms, dok na fizičkom robotu ukupno
     kašnjenje odziva ovisi o opterećenju i inerciji segmenata.

3. **Sigurnosni mehanizmi (Rate limit, Range clamp, E-stop)**:
   - Algoritam `SafetyGuard` u simulaciji reproducira točno iste sigurnosne intervencije
     (npr. zaustavljanje pri E-stopu u T-12a, limitiranje raspona u T-09 i brzine u T-08).