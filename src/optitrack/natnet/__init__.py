"""Minimal, self-contained NatNet (OptiTrack/Motive) decoding + client.

Scoped to what the seminar needs: named hand markers from the MarkerSets section
of frame-of-data, with marker names resolved from the model definition. Those two
layouts are stable across NatNet v2-v4 (MarkerSets are the first datasets), so the
decoder is version-robust without parsing the later, version-specific sections.
"""
