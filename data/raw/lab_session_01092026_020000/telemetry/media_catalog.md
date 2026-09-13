# Video and Photo Record of the Lab Session (Dual-Stream Catalog)

The media recordings document the **21 physical experiments** performed on the UR3e robot. Each run has synchronized video coverage:
1. **Physical view (`data/processed/video_clips_01092026/camera/*.mp4`):** External camera recording the human operator and UR3e robot reacting in physical space (all 21 runs cut from master recording).
2. **OptiTrack Motive screen recording (`data/processed/video_clips_01092026/optitrack_screen/*.mp4`):** Real-time screen capture of Motive 3.0.1 showing 3D rigid body tracking, marker topology, and local coordinate frames (20 runs cut from master MKVs; T4c screen recording was omitted during capture).

---

## Dual-Stream Video $\rightarrow$ Public Test Mapping

| Public ID | Internal ID | Camera Clip (`data/processed/video_clips_01092026/camera/`) | OptiTrack Screen Clip (`data/processed/video_clips_01092026/optitrack_screen/`) | Test Description |
|---|---|---|---|---|
| **T1a** | T-02 | `T1a_natural_tempo.mp4` | `T1a_natural_tempo.mp4` | 6-DOF mimicry, natural tempo (tracking fidelity baseline) |
| **T1b** | T-03 | `T1b_joint_walkthrough.mp4` | `T1b_joint_walkthrough.mp4` | 6-DOF mimicry, joint walkthrough (isolated joint-by-joint motion) |
| **T2a** | T-04 | `T2a_filter_one_euro.mp4` | `T2a_filter_one_euro.mp4` | Filter benchmark — One-Euro (optimal jitter/lag tradeoff) |
| **T2b** | T-05 | `T2b_filter_none.mp4` | `T2b_filter_none.mp4` | Filter benchmark — No filter (raw mocap, high motor jitter) |
| **T2c** | T-06 | `T2c_filter_butterworth.mp4` | `T2c_filter_butterworth.mp4` | Filter benchmark — Butterworth 2nd order (high phase lag) |
| **T2d** | T-07 | `T2d_filter_ema.mp4` | `T2d_filter_ema.mp4` | Filter benchmark — EMA $\alpha=0.2$ (simple smoothing) |
| **T3a** | T-08 | `T3a_rate_limit.mp4` | `T3a_rate_limit.mp4` | Safety layer — Joint rate limiter ($25^\circ/\text{s}$) |
| **T3b** | T-09 | `T3b_range_limit.mp4` | `T3b_range_limit.mp4` | Safety layer — Joint range clamp ($\pm 25^\circ$) |
| **T3c** | T-10 | `T3c_marker_occlusion.mp4` | `T3c_marker_occlusion.mp4` | Safety layer — Marker occlusion fail-safe (5.0 s upper-arm hold) |
| **T3d** | T-12a | `T3d_estop.mp4` | `T3d_estop.mp4` | Safety layer — Emergency stop (software trigger at 10.0 s + teach pendant) |
| **T6** | T-20 | `T6_step_response.mp4` | `T6_step_response.mp4` | Dynamic step response — 5 sudden operator arm flicks |
| **T4a** | T-13a | `T4a_latency_0ms.mp4` | `T4a_latency_0ms.mp4` | Added latency sweep +0 ms (baseline: $\tau_\text{system} = 385\text{ ms}$) |
| **T4b** | T-13b | `T4b_latency_50ms.mp4` | `T4b_latency_50ms.mp4` | Added latency sweep +50 ms |
| **T4c** | T-13c | `T4c_latency_100ms.mp4` | *(screen capture omitted)* | Added latency sweep +100 ms |
| **T4d** | T-13d | `T4d_latency_200ms.mp4` | `T4d_latency_200ms.mp4` | Added latency sweep +200 ms (transition to move-and-wait) |
| **T4e** | T-13e | `T4e_latency_400ms.mp4` | `T4e_latency_400ms.mp4` | Added latency sweep +400 ms (move-and-wait strategy, $\tau = 785\text{ ms}$) |
| **T5a** | T-14 | `T5a_packet_loss_0pct.mp4` | `T5a_packet_loss_0pct.mp4` | Packet loss block — 0% loss baseline |
| **T5b** | T-15 | `T5b_packet_loss_5pct.mp4` | `T5b_packet_loss_5pct.mp4` | Packet loss block — 5% loss |
| **T5c** | T-16 | `T5c_packet_loss_10pct.mp4` | `T5c_packet_loss_10pct.mp4` | Packet loss block — 10% loss |
| **T5d** | T-17 | `T5d_packet_loss_20pct.mp4` | `T5d_packet_loss_20pct.mp4` | Packet loss block — 20% loss |
| **T5e** | T-18 | `T5e_packet_loss_30pct.mp4` | `T5e_packet_loss_30pct.mp4` | Packet loss block — 30% loss |

---

## Still Photographs and Visual Figures

| File | Use in Report |
|---|---|
| `person_and_robot.jpg` | Operator and UR3e in shared workspace $\rightarrow$ `docs/figures/setup_photo.jpg` |
| `markers_colored.png` + `optitrack_rigidbodys.png` | 2-panel physical marker setup + Motive 3D digital twin $\rightarrow$ `docs/figures/markers_digital_twin.png` |
| `markers_left.jpg` | Detail crop fallback $\rightarrow$ `docs/figures/markers_detail_crop.jpg` |

