"""Turning ASCII-art globe with the field lines of its magnetic dipole.

The dipole axis is tilted from the rotation axis, like the Earth's, and turns
with the Earth. Its field lines, r = L cos^2(latitude) in the dipole frame,
fade out where they pass behind the Earth.

Usage:
    uv run globe_magnetique.py            # 30 s videos in outputs/
    uv run globe_magnetique.py --preview  # one PNG frame, fast
"""

import numpy as np

from ascii_earth import DepthLines, HeroGlobe, project_line

DIPOLE_TILT = 11  # angle between the dipole and the rotation axis, degrees
DIPOLE_LON = -72  # longitude towards which the dipole axis leans, degrees
# L: distance where each field line crosses the magnetic equator. A line meets
# the surface at magnetic latitude arccos(sqrt(1 / L)): 30, 40, 46, 55, 63 degrees.
# The largest loops leave the picture, and fade out before its edge (OUTER).
SHELLS = [1.35, 1.7, 2.1, 3.0, 5.0]
OUTER = (2.2, 0.45)  # lines fade out towards this radius on screen, over this width
MAGNETIC_LONS = np.arange(0, 360, 60)  # one field line per shell and per longitude
LIMB = 0.15  # behind the Earth, lines fade out over this width before its edge


def field_lines():
    """Field lines of the dipole, in the Earth frame: list of (n, 3) arrays,
    each going from the southern to the northern end."""
    tilt, lean = np.radians(DIPOLE_TILT), np.radians(DIPOLE_LON)
    # Dipole frame to Earth frame: tilt about the y axis, then turn to DIPOLE_LON
    rot_y = np.array([[np.cos(tilt), 0, np.sin(tilt)], [0, 1, 0],
                      [-np.sin(tilt), 0, np.cos(tilt)]])
    rot_z = np.array([[np.cos(lean), -np.sin(lean), 0], [np.sin(lean), np.cos(lean), 0],
                      [0, 0, 1]])
    lines = []
    for shell in SHELLS:
        edge = np.arccos(np.sqrt(1 / shell))  # latitude where the line meets the surface
        lat = np.linspace(-edge, edge, 240)
        r = shell * np.cos(lat) ** 2
        for lon in np.radians(MAGNETIC_LONS):
            xyz = np.column_stack([r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon),
                                   r * np.sin(lat)])
            lines.append(xyz @ (rot_z @ rot_y).T)
    return lines


class MagneticGlobe(HeroGlobe):
    """Turning ASCII-art globe with the field lines of its magnetic dipole."""

    name = "globe_magnetique"
    preview = 0.1

    def __init__(self):
        super().__init__()
        self.lines_xyz = field_lines()
        self.field = DepthLines(self.ax, limb=LIMB, outer=OUTER)

    def frame(self, t):
        lon0 = super().frame(t)
        # Field lines, turning with the Earth
        self.field.draw([project_line(xyz, lon0, hide=False) for xyz in self.lines_xyz])


if __name__ == "__main__":
    MagneticGlobe.main()
