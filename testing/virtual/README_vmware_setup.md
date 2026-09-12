# 11 — Priprema i testiranje u VMware (URSim)

Ovaj vodič opisuje korake za pokretanje i testiranje cijelog real-time pipelinea u **URSim simulatoru unutar VMware-a** (pokriva zahtjeve **Varijante A / Faza 4** zadatka).

---

## 1. Postavljanje VMware virtualne mašine

### A. Mrežni adapter u VMware-u
1. Otvori postavke VM-a u VMware-u (*Virtual Machine Settings* -> *Network Adapter*).
2. Odaberi **Bridged** (ako su host i VM na istoj lokalnoj mreži) ili **NAT / Host-Only**.
3. U Linux terminalu unutar VM-a provjeri dodijeljeni IP:
   ```bash
   ip a
   # ili
   ifconfig
   ```
   *(Zabilježi IP adresu, npr. `192.168.208.128`)*.

### B. Pokretanje i priprema URSim-a
1. Pokreni URSim unutar VM-a (skripta `start-ursim.sh` ili ikona simulatora za UR3/UR3e).
2. U PolyScope sučelju:
   * **Uključi robota**: Klikni donji lijevi crveni indikator -> **Power On** -> **Release Brakes** (indikator postaje zelen / *Normal*).
   * **Omogući Remote Control mod** (za UR3e / PolyScope 5.x):
     1. Hamburger meni (≡) -> **Settings** -> **System** -> **Remote Control** -> **Enable**.
     2. Gornji desni preklopnik prebaci na **Remote Control**.
   * Postavi robota u početnu pozu (prazan radni prostor).

---

## 2. Provjera veze s Windows računala (Host)

Otvori PowerShell u korijenu repozitorija (`hri-seminar`):

### Korak 1: Ping
```powershell
ping <URSIM_IP>
```

### Korak 2: Provjera RTDE receive veze (bez gibanja)
```powershell
.venv/Scripts/python -m src.tools.check_ursim --ip <URSIM_IP> --no-move
```
*Očekivano: `✓ Povezano. Robot mode=7 safety mode=1 ...`*

### Korak 3: Provjera RTDE servoJ upravljanja (mali sweep ±5°)
```powershell
.venv/Scripts/python -m src.tools.check_ursim --ip <URSIM_IP>
```
*Očekivano: URSim u prozoru izvodi lagani sinusni pomak na J5 zglobu i javlja `✓ Sweep završen, servoStop OK.`*

---

## 3. Scenariji testiranja na URSim-u

### Scenarij A: 1-DOF Replay test (stara snimka šake -> J4)
Nije potreban Motive. Koristi snimljeni CSV u petlji i šalje kut u URSim uz puni logging:

```powershell
.venv/Scripts/python -m src.pipeline.main --sink ursim --ip <URSIM_IP> --seconds 30 --latency-csv data/raw/lab_session_01092026_020000/telemetry/ursim_replay.csv --track-csv data/raw/lab_session_01092026_020000/telemetry/ursim_replay.track.csv --log-actual
```

### Scenarij B: 6-DOF Sintetički test (Mock arm -> svih 6 zglobova)
Simulira prirodno kretanje cijele ruke u realnom vremenu bez OptiTrack hardvera.

* **Terminal 1 (Mock izvor):**
  ```powershell
  .venv/Scripts/python -m src.tools.live_sender --mock-arm --port 51000
  ```
* **Terminal 2 (Pipeline prema URSim-u):**
  ```powershell
  .venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink ursim --ip <URSIM_IP> --mode multi_joint --seconds 30 --range-dps 30 --max-speed-dps 25 --latency-csv data/raw/lab_session_01092026_020000/telemetry/ursim_mock6dof.csv --track-csv data/raw/lab_session_01092026_020000/telemetry/ursim_mock6dof.track.csv --log-actual
  ```

### Scenarij C: Živi Motive/OptiTrack -> URSim (ako je Motive spojen)
* **Terminal 1 (Most prema Motiveu):**
  ```powershell
  .venv/Scripts/python -m src.tools.live_sender --sdk --server-ip 192.168.40.31 --client-ip 192.168.40.30 --port 51000
  ```
* **Terminal 2 (Pipeline prema URSim-u — lakat na J3):**
  ```powershell
  .venv/Scripts/python -m src.pipeline.main --external --port 51000 --sink ursim --ip <URSIM_IP> --joint 2 --seconds 60 --range-dps 30 --max-speed-dps 25 --latency-csv data/raw/lab_session_01092026_020000/telemetry/T-01_ursim.csv --track-csv data/raw/lab_session_01092026_020000/telemetry/T-01_ursim.track.csv --log-actual
  ```

---

## 4. Testiranje sigurnosnih mehanizama (Dokaz za Varijantu A)

| Test | Komanda / Postupak | Očekivani dokaz u logu |
|---|---|---|
| **Rate-limit** | Dodaj `--max-speed-dps 15` uz brze promjene | `ratelim_J*` zastavice u `track.csv` |
| **Range-limit** | Dodaj `--range-dps 20` | `rangeclamp_J*` zastavice u `track.csv` |
| **Fail-safe** | Ugasi Terminal 1 (izvor) usred runa | `halted` zastavica, robot drži poziciju |
| **Softverski E-stop** | Dodaj `--estop-after 10` uz `--seconds 20` | Robot staje nakon 10 s, `halted = 1` |

---

## 5. Analiza vjernosti i generiranje grafova

Nakon svakog testa sa zastavicom `--track-csv`, pokreni:
```powershell
.venv/Scripts/python -m src.tools.track_analysis data/raw/lab_session_01092026_020000/telemetry/ursim_replay.track.csv
```
Alat izračunava:
* **RMSE** i maksimalno odstupanje (ulaz vs stvarni kut robota)
* **Lag / fazno kašnjenje** (cross-correlation)
* Generira usporedni grafikon u `.png` formatu.
