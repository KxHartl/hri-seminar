# 04 — TROUBLESHOOTING (brza rješenja)

| Simptom | Uzrok | Rješenje |
|---|---|---|
| `ur_rtde: Please enable remote control` | Robot u Local modu | PolyScope gornji-desni prekidač → **Remote Control** (+ Settings→System→Remote Control→Enable) |
| RTDE connect visi/ne spaja | Krivi IP / robot off / nije remote | `ping <UR3e>`; provjeri power+brake release; remote ON |
| `check_ursim` receive OK ali control faila | Remote control off ili program blokira | uključi remote; u PolyScope zaustavi pokrenuti program |
| `WinError 10013` na bind porta | Port u Windows rezerviranom rasponu | koristi **51000** (provjereno slobodan) ili `netsh int ipv4 show excludedportrange protocol=udp` |
| Pipeline `primljeno=0` (Faza 1) | Bridge ne šalje / krivi port | provjeri Terminal A radi; isti `--port` na oba; host `127.0.0.1` ako isti PC |
| Pipeline `primljeno=0` (Faza 2) | NatNet ne stiže | Motive Streaming ON; provjeri multicast/unicast i `--multicast`; `--client-ip` = pravi NIC; firewall |
| `NatNet: nema MODELDEF odgovora` | Krivi server IP / verzija / blokiran command port | provjeri `--server-ip`, NatNet verziju, da su portovi 1510/1511 prohodni |
| `NatNet model nema markere [...]` | Imena markera se ne poklapaju | uredi `source.live.marker_name_map` (naše ime → substring stvarnog imena) |
| Robot se trza / oscilira | Premali filter ili prejak gain | pojačaj filtriranje (one_euro `min_cutoff` niže / `butterworth` niži cutoff); smanji `mapping.gain` |
| Robot se jedva miče | Prenizak rate-limit ili gain | povećaj `safety.max_joint_speed_dps` postupno; provjeri `mapping.gain` |
| Krivi smjer gibanja | Predznak mapiranja | `mapping.invert: true` |
| Latencija besmislena (ogromna/negativna) | Bridge i pipeline na različitim PC (satovi) | pokreni oba na istom PC ili NTP; vidi 03_DATA_COLLECTION |
| Hrvatski znakovi ruše ispis | cp1252 konzola | alati već rade `reconfigure(utf-8)`; ako custom skripta — `PYTHONIOENCODING=utf-8` |
| Robot ne staje na gubitak signala | Predug timeout | smanji `safety.signal_timeout_s` (npr. 0.1) |

## Zlatna pravila
- Kad nešto ne radi: **prvo `check_ursim`** (izolira robot-stranu) pa tek onda izvor.
- Mijenjaj **jedan parametar po runu** (lakše za rad i analizu).
- Ako robot radi nešto neočekivano → **e-stop**, pa dijagnoza. Sigurnost > podatak.
