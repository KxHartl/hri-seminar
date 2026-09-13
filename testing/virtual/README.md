# testing/virtual — testiranje u simulatoru (URSim)

Skripte za izvođenje i analizu **6-DOF slobodnog gibanja** u simulatoru **URSim**
(unutar VMware virtualne mašine). Isti cjevovod kao na stvarnom robotu — mijenja se
samo odredište, pa se sve može uvježbati bez hardvera.

Instalacija VMwarea i URSim-a: [`README_vmware_setup.md`](README_vmware_setup.md).

---

## Preduvjeti

1. **URSim pokrenut** u Linux VM-u (zadana adresa: `192.168.208.128`).
2. U PolyScope sučelju:
   - Robot uključen (**Power On** → **Release Brakes**).
   - **Remote Control** mod omogućen
     (☰ → *Settings* → *System* → *Remote Control* → *Enable*, preklopnik na *Remote*).
3. Python okruženje pripremljeno iz korijena repozitorija (`py -3.10 -m venv .venv`,
   `pip install -r requirements.txt`).

---

## Pregled skripti

Pokreću se iz ovog direktorija: `cd testing\virtual\scripts`.

| Skripta | Robot se giba? | Namjena |
|---|:---:|---|
| [`00_ursim_check.ps1`](scripts/00_ursim_check.ps1) | ne | Provjera pinga i stanja robota, bez gibanja |
| [`00_ursim_quicktest.ps1`](scripts/00_ursim_quicktest.ps1) | **da** (`-NoMove` = ne) | Brza provjera ispravnosti veze i servoJ-a |
| [`01_ursim_home.ps1`](scripts/01_ursim_home.ps1) | **da** | Vraćanje u referentnu pozu ravne ruke |
| [`02_free_6dof_mock.ps1`](scripts/02_free_6dof_mock.ps1) | **da** | **Glavno 6-DOF testiranje bez vanjskog hardvera** (sintetički pokret) |
| [`03_free_6dof_live.ps1`](scripts/03_free_6dof_live.ps1) | **da** | 6-DOF sa živim Motive/OptiTrack streamom prema URSim-u |
| [`04_safety_tests_6dof.ps1`](scripts/04_safety_tests_6dof.ps1) | **da** | Verifikacija 4 sigurnosna sloja (brzina, raspon, e-stop, timeout) |
| [`05_plot_analysis.ps1`](scripts/05_plot_analysis.ps1) | ne | Analiza i grafovi za snimljeni `.track.csv` |
| `scripts/_common.ps1` | — | Zajedničke funkcije; ne pokreće se izravno |

### Primjeri

```powershell
cd testing\virtual\scripts

# Provjera veze bez gibanja
.\00_ursim_check.ps1 -UrsimIp 192.168.208.128

# 6-DOF sintetički pokret, 30 s
.\02_free_6dof_mock.ps1 -Seconds 30

# Samo test ograničenja brzine
.\04_safety_tests_6dof.ps1 -Test ratelimit
```

---

## Parametri za `02_free_6dof_mock.ps1`

| Parametar | Zadano | Značenje |
|---|---|---|
| `-UrsimIp` | `192.168.208.128` | Adresa URSim virtualne mašine |
| `-Seconds` | `0` | Trajanje; **`0` = kontinuirano**, prekid s `Ctrl+C` |
| `-RangeDps` | `90` | Dopušteni ± otklon oko početne poze po zglobu [°] |
| `-SpeedDps` | `150` | Gornja granica brzine zgloba [°/s] |
| `-Filter` | `one_euro` | `one_euro` \| `butterworth` \| `ema` \| `none` |
| `-DropRate` | `0.0` | Simulirani gubitak UDP paketa (npr. `0.1` = 10 %) |
| `-AddedLatencyMs` | `0` | Umjetno dodano mrežno kašnjenje [ms] |
| `-NoHome` | — | Preskoči povratak u referentnu pozu |

`04_safety_tests_6dof.ps1` prima `-Test all|ratelimit|rangelimit|estop|failsafe`.

---

## Gdje završavaju podaci

| Skripta | Izlaz |
|---|---|
| `02`, `03` | [`scripts/results/`](scripts/results/) — `<tag>_<datum>.{csv,track.csv,track.png,summary.json}` |
| `04` | `scripts/results/safety/` — po jedan zapis za svaki sigurnosni test |

Rezultati simulacijskih runova korišteni u radu arhivirani su u
[`data/processed/simulation_runs_31082026/`](../../data/processed/simulation_runs_31082026/),
a usporedba simulacije sa stvarnim robotom u
[`data/processed/sim_comparison_04092026/`](../../data/processed/sim_comparison_04092026/).
