# Testing Framework (`testing/`)

This directory contains the automated and manual testing suites for real-time OptiTrack-to-Universal Robots teleoperation.

---

## Directory Overview

```
testing/
├── lab/                               # Physical robot testing (UR3e Cobot + OptiTrack)
│   ├── scripts/                       # Execution scripts
│   │   ├── run_all_tests.ps1          # Automated execution runner for the 21-run test matrix
│   │   ├── 00_check.ps1               # Hardware connection and RTDE connectivity probe
│   │   ├── 01_home.ps1                # Safe positioning to canonical home pose
│   │   ├── 02_free_motion.ps1         # Manual free-motion tracking validation
│   │   ├── 03_joint_walkthrough.ps1   # Isolated joint-by-joint validation
│   │   ├── 04_axis_calibration.ps1    # Segment and Euler axis calibration
│   │   └── 05_free_6dof.ps1           # Continuous 6-DOF live teleoperation
│   ├── protocols/                     # Standard Operating Procedures & Runbooks
│   │   ├── 01_preflight.md            # Pre-session hardware checklist
│   │   ├── 02_setup.md                # Network, Motive, and robot configuration
│   │   ├── 03_test_protocol.md        # Step-by-step test execution guidelines
│   │   ├── 04_data_collection.md      # Data recording and backup procedure
│   │   ├── 05_troubleshooting.md      # Common failure modes and recovery steps
│   │   ├── 06_live_optitrack.md       # Live NatNet streaming instructions
│   │   ├── 07_demo_runbook.md         # Live demonstration runbook
│   │   ├── 08_session_plan.md         # Master experimental test matrix plan (T-01 … T-21)
│   │   ├── 08_future_test_proposals.md# Proposed experiments that were not performed
│   │   ├── 09_motive_setup.md         # Motive 3.0.1 camera calibration & rigid body setup
│   │   ├── 10_subjective_evaluation.md# Operator and observer pHRI evaluation logs
│   │   └── cheatsheet.md              # Quick-reference command cheat sheet
│   ├── diag/                          # Diagnostic utilities (NatNet, SDK, axes)
│   └── templates/                     # Protocol logs and questionnaire templates
│
└── virtual/                           # Simulation suite (VMware URSim)
    ├── README.md                      # Virtual testing guide and network setup
    ├── README_vmware_setup.md         # VMware workstation & URSim installation guide
    └── scripts/                       # Simulation automation scripts
        ├── 00_ursim_check.ps1         # Ping and RTDE state probe for URSim
        ├── 00_ursim_quicktest.ps1     # Quick sanity test on URSim
        ├── 01_ursim_home.ps1          # Move simulated robot to home pose
        ├── 02_free_6dof_mock.ps1      # 6-DOF teleoperation with synthetic motion
        ├── 03_free_6dof_live.ps1      # 6-DOF teleoperation with live mocap stream
        ├── 04_safety_tests_6dof.ps1   # Verification of safety limiters in simulation
        └── 05_plot_analysis.ps1       # Telemetry plotting and analysis
```

---

## Instructions

Run the scripts from their own directory; each one loads `_common.ps1` from `$PSScriptRoot`.

### 1. Virtual Simulation (URSim)
```powershell
cd testing\virtual\scripts

# Verify connection to the URSim virtual machine (no motion)
.\00_ursim_check.ps1 -UrsimIp 192.168.208.128

# Rehearse 6-DOF motion with the mock input generator
.\02_free_6dof_mock.ps1 -UrsimIp 192.168.208.128 -Seconds 30
```

### 2. Physical Robotics Lab (UR3e)
```powershell
cd testing\lab\scripts

# Preflight hardware and network check (no motion)
.\00_check.ps1 -RobotIp 192.168.40.50 -MotiveIp 192.168.40.31

# Move robot to canonical ready pose
.\01_home.ps1 -RobotIp 192.168.40.50

# Run the complete automated test matrix (T-02 … T-20)
.\run_all_tests.ps1
```

The scripts write into `testing/lab/results/` and `testing/virtual/scripts/results/`
(created on first run). Telemetry from the physical session of 1–2 Sep 2026 was archived
to `data/raw/lab_session_01092026_020000/telemetry/` — that is where the figures quoted
in the paper come from.
