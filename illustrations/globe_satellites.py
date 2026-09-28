"""Turning ASCII-art globe with satellites on their orbits.

The orbits are fixed in space and the Earth turns once under them during the
video. Each satellite goes round its orbit a whole number of times, lower
orbits faster, and the geostationary one exactly once, keeping pace with the
Earth: the video loops. Behind each satellite, the arc it has just travelled.

Usage:
    uv run globe_satellites.py            # 30 s videos in outputs/
    uv run globe_satellites.py --preview  # one PNG frame, fast
"""

import numpy as np

from ascii_earth import (ACCENT, DURATION, LINE_WIDTH, MARK, MARK_FONTSIZE, GlyphLayer,
                         HeroGlobe, project_xyz)

# Circular orbits: radius (Earth radii, not to scale), inclination, right
# ascension of the ascending node, satellite position along the orbit at t = 0
# (degrees), turns during the video, and the satellite's symbol
ORBITS = [
    (1.25, 98, 30, 310, 4, "+"),   # polar, low: Earth observation
    (1.45, 30, -60, 160, 3, "*"),  # inclined, low
    (1.70, 55, 120, 200, 2, "@"),  # inclined, medium: navigation
    (2.05, 0, 0, 130, 1, "&"),     # equatorial, high: geostationary
]
ORBITS_LON0 = 10  # the orbits are seen from this longitude (their orientation is arbitrary)
TRAIL = 270  # length of the orbit drawn behind each satellite, degrees
GAP = 0.15  # space on screen between an orbit and its satellite, in Earth radii


def orbit_xyz(radius, inclination, node, anomaly):
    """3D positions (Earth frame) on a circular orbit, anomaly in degrees."""
    u, i, o = np.radians(anomaly), np.radians(inclination), np.radians(node)
    x, y = np.cos(u), np.sin(u)
    x, y, z = x, y * np.cos(i), y * np.sin(i)
    x, y = x * np.cos(o) - y * np.sin(o), x * np.sin(o) + y * np.cos(o)
    return radius * np.stack([x, y, z], axis=-1)


class SatelliteGlobe(HeroGlobe):
    """Turning ASCII-art globe with satellites on their orbits."""

    name = "globe_satellites"
    preview = 0.0

    def __init__(self):
        super().__init__()
        self.sats = GlyphLayer(self.ax, MARK_FONTSIZE * 1.8, zorder=4, weight="bold")
        # Two lines per orbit: the part behind the Earth and the part in front
        self.trails = [[self.ax.plot([], [], color=ACCENT, linewidth=LINE_WIDTH,
                                     solid_capstyle="round", zorder=zorder)[0]
                        for zorder in (1, 3)] for _ in ORBITS]

    def frame(self, t):
        super().frame(t)
        sx, sy, chars = [], [], []
        for (radius, inclination, node, position, laps, char), lines in zip(ORBITS,
                                                                           self.trails):
            now = position + 360 * laps * t / DURATION
            anomaly = np.linspace(now - TRAIL, now, 600)
            ox, oy, depth = project_xyz(orbit_xyz(radius, inclination, node, anomaly),
                                        ORBITS_LON0)
            hidden = (depth < 0) & (np.hypot(ox, oy) < 1.0)
            hidden |= np.hypot(ox - ox[-1], oy - oy[-1]) < GAP  # room for the satellite
            for line, in_front in zip(lines, (False, True)):
                keep = ~hidden & ((depth >= 0) == in_front)
                line.set_data(np.where(keep, ox, np.nan), np.where(keep, oy, np.nan))
            # The satellite, unless the Earth hides it
            if not (depth[-1] < 0 and np.hypot(ox[-1], oy[-1]) < 1.02):
                sx.append(ox[-1])
                sy.append(oy[-1])
                chars.append(char)
        self.sats.draw(sx, sy, chars, np.full(len(chars), MARK))


if __name__ == "__main__":
    SatelliteGlobe.main()
