"""Reference-pose config handling (src/tools/home_pose.py).

The rewrite is a targeted line edit rather than a YAML dump, so the thing worth
testing is that it keeps the file loadable and keeps the comment that explains
what the pose means.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from src.tools.home_pose import read_home_deg, write_home_deg

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_default_config_has_reference_pose():
    home = read_home_deg(REPO_ROOT / "src/config/default.yaml")
    assert home is not None and len(home) == 6


def test_write_replaces_values_and_keeps_comment(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "robot:\n"
        "  sink: ur3e\n"
        "  home_q_deg: [250, -180, 0, 0, 90, 0]   # ravna ispružena ruka\n"
        "  control_hz: 125\n",
        encoding="utf-8",
    )

    write_home_deg([1.5, -2, 0, 0, 90.25, 0], cfg)

    text = cfg.read_text(encoding="utf-8")
    assert "# ravna ispružena ruka" in text
    assert "control_hz: 125" in text
    loaded = yaml.safe_load(text)
    assert loaded["robot"]["home_q_deg"] == [1.5, -2, 0, 0, 90.25, 0]
    assert read_home_deg(cfg) == [1.5, -2.0, 0.0, 0.0, 90.25, 0.0]
