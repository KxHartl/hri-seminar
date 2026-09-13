# data/sources — literatura seminara

13 recenziranih radova korištenih u seminaru, preuzetih kao PDF. Kolegij traži
**najmanje 5 znanstvenih radova, ne starijih od 5 godina (≥ 2021)**, iz izvora
IEEE / Springer / Elsevier / ACM.

| Gdje | Što |
|---|---|
| [`../SOURCES_LOG.md`](../SOURCES_LOG.md) | **Popis s izvorom, naslovom, autorima, venueom, godinom, DOI-jem i statusom** za svaki rad |
| [`../../docs/references.bib`](../../docs/references.bib) | BibTeX baza (16 unosa, uklj. normu ISO/TS 15066), stil `ieeetr` |
| [`../../TASK/LITERATURE.md`](../../TASK/LITERATURE.md) | Koji se rad koristi u kojem poglavlju seminara |

## Datoteke

```
Ghanbarzadeh2024_VarImpedance_ISO15066.pdf        Glawe2026_Autonomy_SenseOfAgency_HRI.pdf
Lee2025_WebRTC_Latency_RemoteSurgery.pdf          Louca2024_HapticHighLatency_Teleop.pdf
Martini2024_RobustFilter_HRI_Tracking.pdf         Saccuti2025_BinocularVision_SSM_HRC.pdf
Stroppa2023_SharedControl_SoftGrowingRobot.pdf    Vieira2024_SmartphoneMocap_vs_OptiTrack_Gait.pdf
Wang2024_BilateralTeleop_TimeVaryingDelay.pdf     Weigend2023_ArmPose_Smartwatch_RobotControl.pdf
Weigend2024_iRoCo_Smartwatch_RobotControl.pdf     Zaman2025_EnhancedTeleop_MasterSlave_UR10e.pdf
Zhu2022_IMU_TremorAttenuation_Teleop.pdf
```

## ⚠️ Ime datoteke nije mjerodavno

Za povezivanje PDF-a s citatom mjerodavno je polje `file` u
[`../../docs/references.bib`](../../docs/references.bib), **ne ime datoteke**.
Šest PDF-ova nosi u imenu drugog prvog autora ili drugu godinu od svog cite keya:

| Datoteka | Cite key |
|---|---|
| `Vieira2024_…` | `castillo2025` |
| `Lee2025_…` | `shi2025` |
| `Zaman2025_…` | `zainudin2025` |
| `Saccuti2025_…` | `peng2025` |
| `Ghanbarzadeh2024_…` | `ghanbarzadeh2025` |
| `Wang2024_…` | `wang2025` |

Provjerom naslovnica utvrđeno je da su **cite keyevi točni**, a imena datoteka
zaostala iz preuzimanja. Pet PDF-ova su arXiv preprinti (`ghanbarzadeh2025`,
`weigend2023`, `weigend2024`, `martini2024`, `stroppa2023`) — oznake `str.~N` u radu
odnose se na stranicu preprinta, koja se ne mora poklapati s objavljenom verzijom.
Detalji: [`../SOURCES_LOG.md`](../SOURCES_LOG.md).

## Git LFS

Datoteke u ovom direktoriju prate se preko **Git LFS**. Bez `git lfs install`
prije kloniranja stižu samo kao tekstualni pokazivači, a ne kao PDF-ovi.
