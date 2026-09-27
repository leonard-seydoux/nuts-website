"""Turning ASCII-art globe with the field lines of its magnetic dipole.

The dipole axis is tilted from the rotation axis, like the Earth's, and turns
with the Earth. Its field lines, r = L cos^2(latitude) in the dipole frame,
are solid lines, fading out where they pass behind the Earth. Same format as the other hero
videos (globe_*.py): transparent, square, same Earth, and it loops.

Usage:
    uv run globe_magnetique.py            # 30 s videos in outputs/
    uv run globe_magnetique.py --preview  # one PNG frame, fast
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt

from ascii_earth import (ACCENT, C9, DepthLines, GlyphLayer, fibonacci_sphere,
                         is_land, orthographic_xy, render_transparent_video)
from globe_axes import BACK_ALPHA
from globe_seismes import (DPI, DURATION, EXTENT, FONTSIZE, FPS, LAND, LAND_CHARS,
                           LAT0, LON_START, N_POINTS, OCEAN, OCEAN_CHARS, OUTPUT,
                           RING_WIDTH, SIZE, STYLES, WEIGHT, shade)
from sections import project_xyz

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


class MagneticGlobe:
    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.lat, self.lon = fibonacci_sphere(N_POINTS)
        self.land = is_land(self.lat, self.lon)
        self.chars = np.where(self.land,
                              rng.choice(list(LAND_CHARS), N_POINTS),
                              rng.choice(list(OCEAN_CHARS), N_POINTS))
        self.lines_xyz = field_lines()

        self.fig = plt.figure(figsize=(SIZE, SIZE), dpi=DPI)
        self.fig.patch.set_alpha(0)  # transparent: the website sets the color
        ax = self.fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(-EXTENT, EXTENT)
        ax.set_ylim(-EXTENT, EXTENT)
        ax.set_aspect("equal")
        ax.axis("off")
        self.surface = GlyphLayer(ax, STYLES, FONTSIZE, zorder=2, weight=WEIGHT)
        self.field = DepthLines(ax, ACCENT, RING_WIDTH, back=BACK_ALPHA, limb=LIMB,
                                outer=OUTER)

    def frame(self, t):
        turn = t / DURATION
        lon0 = (LON_START - 360 * turn + 180) % 360 - 180

        # Surface
        x, y, mu = orthographic_xy(self.lat, self.lon, lon0, LAT0)
        front = mu > 0
        style = np.where(self.land, LAND, OCEAN) + shade(x, y, mu)
        self.surface.draw(x[front], y[front], self.chars[front], style[front])

        # Field lines, turning with the Earth
        polylines = []
        for xyz in self.lines_xyz:
            lx, ly, depth = project_xyz(xyz, lon0, LAT0)
            polylines.append((lx, ly, depth / np.linalg.norm(xyz, axis=1)))
        self.field.draw(polylines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", action="store_true", help="render one frame as PNG")
    args = parser.parse_args()

    OUTPUT.mkdir(exist_ok=True)
    globe = MagneticGlobe()
    if args.preview:
        globe.frame(DURATION * 0.1)
        globe.fig.savefig(OUTPUT / "globe_magnetique.png", transparent=True)
        return
    render_transparent_video(globe.fig, globe.frame, DURATION, FPS,
                             OUTPUT / "globe_magnetique", matte=C9)


if __name__ == "__main__":
    main()
