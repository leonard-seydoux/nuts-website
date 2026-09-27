"""Turning ASCII-art globe with satellites on their orbits.

The animated version of the satellites illustration, for the home page hero.
The orbits are fixed in space and the Earth turns once under them during the
video. Each satellite goes round its orbit a whole number of times, lower
orbits faster, and the geostationary one exactly once, keeping pace with the
Earth: the video loops. Behind each satellite, the arc it has just travelled.
Same format as globe_seismes.py (transparent, square), so the hero can show
any of them.

Usage:
    uv run globe_satellites.py            # 30 s videos in outputs/
    uv run globe_satellites.py --preview  # one PNG frame, fast
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt

from ascii_earth import (ACCENT, C9, GlyphLayer, fibonacci_sphere, is_land,
                         orthographic_xy, render_transparent_video)
from globe_seismes import (DPI, DURATION, EXTENT, FONTSIZE, FPS, LAND, LAND_CHARS,
                           MARK_FONTSIZE, WEIGHT,
                           LAT0, LON_START, N_POINTS, OCEAN, OCEAN_CHARS, OUTPUT,
                           RING_WIDTH, SIZE, STYLES, shade)
from sections import (ORBITS, SAT_CHARS, SAT_GAP, SAT_LON0, SAT_TRAIL, orbit_xyz,
                      project_xyz)

# The orbits are seen from the same side as in the still image (SAT_LON0): their
# orientation in space is arbitrary, and the Earth keeps the shared framing
LAPS = [4, 3, 2, 1]  # turns of each satellite during the video, in the order of ORBITS
SAT_STYLE = len(STYLES)


class SatelliteGlobe:
    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.lat, self.lon = fibonacci_sphere(N_POINTS)
        self.land = is_land(self.lat, self.lon)
        self.chars = np.where(self.land,
                              rng.choice(list(LAND_CHARS), N_POINTS),
                              rng.choice(list(OCEAN_CHARS), N_POINTS))

        self.fig = plt.figure(figsize=(SIZE, SIZE), dpi=DPI)
        self.fig.patch.set_alpha(0)  # transparent: the website sets the color
        ax = self.fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(-EXTENT, EXTENT)
        ax.set_ylim(-EXTENT, EXTENT)
        ax.set_aspect("equal")
        ax.axis("off")
        styles = STYLES + [(ACCENT, 1.0)]
        self.surface = GlyphLayer(ax, styles, FONTSIZE, zorder=2, weight=WEIGHT)
        self.sats = GlyphLayer(ax, styles, MARK_FONTSIZE * 1.8, zorder=4, weight="bold")
        # Two lines per orbit: the part behind the Earth and the part in front
        self.trails = [
            [ax.plot([], [], color=ACCENT, linewidth=RING_WIDTH,
                     solid_capstyle="round", zorder=zorder)[0] for zorder in (1, 3)]
            for _ in ORBITS
        ]

    def frame(self, t):
        turn = t / DURATION

        # The Earth turns under the orbits
        lon0 = (LON_START - 360 * turn + 180) % 360 - 180
        x, y, mu = orthographic_xy(self.lat, self.lon, lon0, LAT0)
        front = mu > 0
        style = np.where(self.land, LAND, OCEAN) + shade(x, y, mu)
        self.surface.draw(x[front], y[front], self.chars[front], style[front])

        sx, sy, sc = [], [], []
        for (radius, inclination, node, position), char, laps, lines in zip(
                ORBITS, SAT_CHARS, LAPS, self.trails):
            now = position + 360 * laps * turn
            anomaly = np.linspace(now - SAT_TRAIL, now, 600)
            ox, oy, depth = project_xyz(orbit_xyz(radius, inclination, node, anomaly),
                                        SAT_LON0, LAT0)
            hidden = (depth < 0) & (np.hypot(ox, oy) < 1.0)
            hidden |= np.hypot(ox - ox[-1], oy - oy[-1]) < SAT_GAP  # room for the satellite
            for line, in_front in zip(lines, (False, True)):
                keep = ~hidden & ((depth >= 0) == in_front)
                line.set_data(np.where(keep, ox, np.nan), np.where(keep, oy, np.nan))
            # The satellite, unless the Earth hides it
            if not (depth[-1] < 0 and np.hypot(ox[-1], oy[-1]) < 1.02):
                sx.append(ox[-1])
                sy.append(oy[-1])
                sc.append(char)
        self.sats.draw(sx, sy, sc, np.full(len(sc), SAT_STYLE))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", action="store_true", help="render one frame as PNG")
    args = parser.parse_args()

    OUTPUT.mkdir(exist_ok=True)
    globe = SatelliteGlobe()
    if args.preview:
        globe.frame(0)
        globe.fig.savefig(OUTPUT / "globe_satellites.png", transparent=True)
        return
    render_transparent_video(globe.fig, globe.frame, DURATION, FPS,
                             OUTPUT / "globe_satellites", matte=C9)


if __name__ == "__main__":
    main()
