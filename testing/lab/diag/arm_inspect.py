"""Calibration helper for the full-arm 6-DOF mapping.

Streams the three arm rigid bodies via the official NatNet SDK, homes on the first
frame (hold a straight arm!), then prints — a few times per second — BOTH:

  RAW   the relative-orientation Euler components per segment, in degrees. Do ONE
        isolated motion at a time (only shoulder up/down, then only left/right, ...)
        and watch which RAW component responds, with what sign and scale. That tells
        you the seq / index / sign to put in ``arm_axes`` (src/config/default.yaml).
  MAPPED the six channels as ArmPoseMapper computes them with the CURRENT config —
        after editing arm_axes, re-run and confirm each isolated motion drives the
        intended channel (and only it).

Shoulder = upper-arm vs world home (Euler ZXY). Wrist = hand vs forearm, home-ref
(Euler XYZ). Elbow = positional angle (deg) + orientation Euler (XYZ) for reference.

Usage:
    python testing/lab/diag/arm_inspect.py <server_ip> <client_ip>
    # lab default: server=192.168.40.31 (Motive)  client=192.168.40.30 (this PC)
"""
from __future__ import annotations

import math
import os
import sys
import time

import numpy as np
import yaml
from scipy.spatial.transform import Rotation

# Repo root on path so 'src' imports work when run as a script.
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.kinematics.arm_pose import CHANNELS, ArmPoseMapper, RigidPose  # noqa: E402
from src.kinematics.segment_angle import elbow_flexion_angle  # noqa: E402
from src.optitrack.sdk_natnet import DEFAULT_IDS, SDKRigidBodyReader  # noqa: E402

server = sys.argv[1] if len(sys.argv) > 1 else "192.168.40.31"
client = sys.argv[2] if len(sys.argv) > 2 else "192.168.40.30"
ids = DEFAULT_IDS
U, F, H = ids["upper"], ids["fore"], ids["hand"]

axes = yaml.safe_load(open(os.path.join(_ROOT, "src/config/default.yaml"),
                           encoding="utf-8")).get("arm_axes")
mapper = ArmPoseMapper(axes)

reader = SDKRigidBodyReader(server, client, use_multicast=False)
home = None
last_print = 0.0
print(f"ARM INSPECT server={server} client={client}  ids U/F/H={U}/{F}/{H}")
print("Drži ISPRUŽENU ruku dok se ne postavi home, pa radi JEDAN pokret po jedan.\n")

try:
    for poses in reader._frames():
        if not all(i in poses for i in (U, F, H)):
            continue
        R_U = Rotation.from_quat(poses[U][1])
        R_F = Rotation.from_quat(poses[F][1])
        R_H = Rotation.from_quat(poses[H][1])
        up = RigidPose(*poses[U]); fo = RigidPose(*poses[F]); ha = RigidPose(*poses[H])

        if home is None:
            home = {"U": R_U, "F": R_F, "H": R_H,
                    "el": elbow_flexion_angle(up.pos, fo.pos, ha.pos)}
            mapper.compute(up, fo, ha)        # mapper homes on this same frame
            print(">>> HOME postavljen. Sad izoliraj pokrete.\n")
            continue

        now = time.time()
        if now - last_print < 0.3:
            continue
        last_print = now

        sh = (home["U"].inv() * R_U).as_euler("ZXY", degrees=True)            # [Z,X,Y]
        wr_rel = (home["F"].inv() * home["H"]).inv() * (R_F.inv() * R_H)
        wr = wr_rel.as_euler("XYZ", degrees=True)                            # [X,Y,Z]
        el_pos = math.degrees(elbow_flexion_angle(up.pos, fo.pos, ha.pos) - home["el"])
        el_rel = (home["U"].inv() * home["F"]).inv() * (R_U.inv() * R_F)
        el_or = el_rel.as_euler("XYZ", degrees=True)
        ch = mapper.compute(up, fo, ha)

        print(f"RAW  rame[Z,X,Y]={sh[0]:7.1f},{sh[1]:7.1f},{sh[2]:7.1f}  "
              f"zglob[X,Y,Z]={wr[0]:7.1f},{wr[1]:7.1f},{wr[2]:7.1f}  "
              f"lakat poz={el_pos:6.1f} or[X,Y,Z]={el_or[0]:6.1f},{el_or[1]:6.1f},{el_or[2]:6.1f}")
        print("MAP  " + "  ".join(f"{c}={math.degrees(ch[c]):6.1f}" for c in CHANNELS) + "\n")
finally:
    reader.close()
