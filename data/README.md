# Data Catalog (`data/`)

Overview of experimental data, motion capture recordings, video streams, and literature.

---

## Directory Overview

```
data/
├── README.md                      # This catalog
├── SOURCES_LOG.md                 # Literature tracking log with DOIs and abstracts
│
├── raw/                           # Raw, immutable sensor and session data
│   ├── lab_session_01092026_020000/
│   │   ├── optitrack/
│   │   │   ├── takes/             # Raw Motive .tak files (calibration & session takes)
│   │   │   └── screen_recordings/ # Raw continuous .mkv screen captures
│   │   ├── photos/                # Camera photos of setup, robot, and markers
│   │   └── telemetry/             # Live 125 Hz robot telemetry (T-02 to T-20)
│   │       ├── run_log.csv        # Run parameters and metadata
│   │       ├── media_catalog.md   # Video-to-telemetry mapping
│   │       ├── exploratory/       # Pre-session exploratory test runs
│   │       └── contact_check/     # Initial contact verification
│   └── reference_mocap/           # Baseline mocap takes from course exercises
│       ├── vjezbe_01/
│       └── vjezbe_02/
│
├── processed/                     # Derived, cut, or modeled data
│   ├── video_clips_01092026/      # Extracted individual test run clips
│   │   ├── camera/                # 21 cut external camera videos (.mp4)
│   │   └── optitrack_screen/      # 20 cut Motive 3D viewport screen captures (.mp4)
│   ├── benchmarks_02092026/       # Filter benchmark results (filter_bench.summary.json)
│   ├── packet_loss_sweep_02092026/# Deterministic packet loss model (L-00 to L-30)
│   ├── simulation_runs_31082026/  # Virtual URSim simulation logs
│   └── sim_comparison_04092026/   # Real UR3e vs. URSim replay comparison
│       ├── COMPARISON_REPORT.md   # Per-run RMSE / lag / correlation write-up
│       ├── comparison_metrics.csv # Same figures as a table (+ .json)
│       ├── manifest.yaml          # Which runs were replayed and how
│       └── telemetry/             # 18 URSim replay runs (.csv, .track.csv, .png)
│
└── sources/                       # 13 peer-reviewed literature PDFs (Git LFS)
```

The run IDs used here (`T-02` … `T-20`) map to the public IDs used in the paper and
video filenames (`T1a` … `T5e`) through
[`raw/lab_session_01092026_020000/telemetry/media_catalog.md`](raw/lab_session_01092026_020000/telemetry/media_catalog.md).
