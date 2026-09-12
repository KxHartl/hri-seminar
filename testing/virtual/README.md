# Virtual Testing Suite (6-DOF URSim)

Ovaj direktorij (`testing/virtual/`) sadrži skripte za izvođenje i analizu **6-DOF slobodnog gibanja** u simulatoru **URSim (unutar VMware virtualne mašine)**.

---

## Preduvjeti u VMware-u

1. **URSim pokrenut** u Linux VM-u na IP adresi (zadano: `192.168.208.128`).
2. U PolyScope sučelju:
   * Robot uključen (**Power On** $\rightarrow$ **Release Brakes**).
   * **Remote Control** mod omogućen (☰ $\rightarrow$ *Settings* $\rightarrow$ *System* $\rightarrow$ *Remote Control* $\rightarrow$ *Enable*, preklopnik na *Remote*).

---

## Pregled skripti

| Skripta | Namjena | Primjer pokretanja |
|---|---|---|
| [`00_ursim_provjera.ps1`](file:///d:/truenas_kresimir_share_cp/FSB/semestar_09/hri-seminar/testing/virtual/scripts/00_ursim_check.ps1) | Provjera pinga i stanja robota bez gibanja | `.\00_ursim_provjera.ps1` |
| [`01_ursim_home.ps1`](file:///d:/truenas_kresimir_share_cp/FSB/semestar_09/hri-seminar/testing/virtual/scripts/01_ursim_home.ps1) | Vraćanje u referentnu pozu ravne ruke | `.\01_ursim_home.ps1 -Yes` |
| [`02_slobodno_6dof_mock.ps1`](file:///d:/truenas_kresimir_share_cp/FSB/semestar_09/hri-seminar/testing/virtual/scripts/02_free_6dof_mock.ps1) | **Glavno 6-DOF testiranje bez vanjskog hardvera** | `.\02_slobodno_6dof_mock.ps1` |
| [`03_slobodno_6dof_live.ps1`](file:///d:/truenas_kresimir_share_cp/FSB/semestar_09/hri-seminar/testing/virtual/scripts/03_free_6dof_live.ps1) | 6-DOF s pravim Motive/OptiTrack streamom prema URSim-u | `.\03_slobodno_6dof_live.ps1` |
| [`04_sigurnosni_testovi_6dof.ps1`](file:///d:/truenas_kresimir_share_cp/FSB/semestar_09/hri-seminar/testing/virtual/scripts/04_safety_tests_6dof.ps1) | Verifikacija 4 sigurnosna sloja (brzina, domet, e-stop, timeout) | `.\04_sigurnosni_testovi_6dof.ps1` |
| [`05_analiza_grafovi.ps1`](file:///d:/truenas_kresimir_share_cp/FSB/semestar_09/hri-seminar/testing/virtual/scripts/05_plot_analysis.ps1) | Analiza i generiranje grafikona za snimljeni `.track.csv` | `.\05_analiza_grafovi.ps1` |

---

## Detalji o parametrima za `02_slobodno_6dof_mock.ps1`

* `-Seconds 0` : Zadani rad je **kontinuiran** (prekida se tipkom `Ctrl+C`). Ako želiš fiksno vrijeme, npr. `-Seconds 30`.
* `-RangeDps 30` : Dopušteni maksimalni $\pm$ otklon oko početne poze po zglobu [$^\circ$].
* `-SpeedDps 30` : Gornja granica brzine zgloba [$^\circ/\text{s}$].
* `-Filter one_euro` : Odabir filtra (`one_euro`, `butterworth`, `ema`, `none`).
* `-DropRate 0.1` : Simulacija gubitka UDP paketa (npr. 10%).
* `-AddedLatencyMs 50` : Simulacija dodatnog mrežnog kašnjenja.

Svi rezultati (`.csv`, `.track.csv`, `.track.png`, `.summary.json`) automatski se spremaju u mapu:
`data/processed/simulation_runs_31082026/`.
