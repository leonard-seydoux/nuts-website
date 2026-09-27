"""Turning ASCII-art globe with a sketch of its rotation.

The rotation axis z goes through the poles and out of the globe; a curved
arrow labelled Omega turns with the Earth above the North Pole; the x and y
axes, in the equatorial plane (towards 0 and 90 degrees East), turn with the
Earth; the equator is a dashed circle fixed in space. Same format as the other hero videos
(globe_*.py): transparent, square, same Earth, and it loops.

Usage:
    uv run globe_axes.py            # 30 s videos in outputs/
    uv run globe_axes.py --preview  # one PNG frame, fast
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt

from ascii_earth import (ACCENT, C9, DepthLines, GlyphLayer, depth_alpha,
                         fibonacci_sphere, is_land, orthographic_xy,
                         render_transparent_video)
from globe_seismes import (DPI, DURATION, EXTENT, FONTSIZE, FPS, LAND, LAND_CHARS,
                           LAT0, LON_START, MARK_FONTSIZE, N_POINTS, OCEAN,
                           OCEAN_CHARS, OUTPUT, RING_WIDTH, SIZE, STYLES, WEIGHT,
                           shade)
from sections import project_xyz

AXIS_LENGTH = 1.75  # the axis sticks out of the globe up to this radius
ARROW_HEIGHT, ARROW_RADIUS = 1.38, 0.32  # curved arrow around the axis, above the pole
ARROW_ARC = 270  # degrees
EQUATOR_RADIUS = 1.2  # dashed equator, fixed in space
BODY_AXES = [("x", 0), ("y", 90)]  # axes turning with the Earth: label, longitude
HEAD = 0.09  # arrowhead length, in Earth radii
BACK_ALPHA = 0.35  # opacity of what passes behind the Earth
LABEL_SIZE = MARK_FONTSIZE * 2.2


def hidden(x, y, depth):
    """Points hidden by the Earth."""
    return (depth < 0) & (np.hypot(x, y) < 1.0)


def head(x, y):
    """Two strokes of an arrowhead at the end of a projected line."""
    d = np.array([x[-1] - x[-2], y[-1] - y[-2]])
    d /= np.linalg.norm(d)
    strokes = []
    for side in (1, -1):
        c, s = np.cos(np.radians(150 * side)), np.sin(np.radians(150 * side))
        wing = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
        strokes.append(([x[-1], x[-1] + HEAD * wing[0]], [y[-1], y[-1] + HEAD * wing[1]]))
    return strokes


class AxesGlobe:
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
        self.ax = ax
        styles = STYLES + [(ACCENT, 1.0)]
        self.surface = GlyphLayer(ax, styles, FONTSIZE, zorder=2, weight=WEIGHT)

        # Lines whose opacity follows their depth, the equator dashed
        self.lines = DepthLines(ax, ACCENT, RING_WIDTH, back=BACK_ALPHA)
        self.equator = DepthLines(ax, ACCENT, RING_WIDTH, back=BACK_ALPHA, dash=0.1)
        label = dict(color=ACCENT, fontsize=LABEL_SIZE, ha="center", va="center", zorder=4)
        self.labels = {name: ax.text(0, 0, f"${name}$", **label)
                       for name in ["z"] + [name for name, _ in BODY_AXES]}
        self.omega = ax.text(0, 0, r"$\Omega$", **label)

    def line(self, xyz, lon0, radius=None):
        """Projected polyline (x, y, mu), with NaN where the Earth hides it."""
        x, y, depth = project_xyz(xyz, lon0, LAT0)
        r = np.linalg.norm(xyz, axis=1) if radius is None else radius
        mu = depth / r
        return np.where(hidden(x, y, depth), np.nan, x), y, mu

    def arrow(self, x, y, mu):
        """A line and its arrowhead, both shaded by the depth of the tip."""
        polylines = [(x, y, mu)]
        if np.isfinite(x[-1]):
            for hx, hy in head(x, y):
                polylines.append((np.array(hx), np.array(hy), np.full(2, mu[-1])))
        return polylines

    def label(self, text, x, y, mu):
        text.set_position((x, y))
        text.set_visible(bool(np.isfinite(x)))
        text.set_alpha(float(depth_alpha(mu, BACK_ALPHA)))

    def frame(self, t):
        turn = t / DURATION
        lon0 = (LON_START - 360 * turn + 180) % 360 - 180

        # Surface
        x, y, mu = orthographic_xy(self.lat, self.lon, lon0, LAT0)
        front = mu > 0
        style = np.where(self.land, LAND, OCEAN) + shade(x, y, mu)
        self.surface.draw(x[front], y[front], self.chars[front], style[front])

        polylines = []
        # Rotation axis z, out of the globe on both sides (inside, the Earth hides it)
        z = np.linspace(1.0, AXIS_LENGTH, 60)
        zeros = np.zeros_like(z)
        north = self.line(np.column_stack([zeros, zeros, z]), LON_START)
        south = self.line(np.column_stack([zeros, zeros, -z]), LON_START)
        polylines += self.arrow(*north) + [south]
        nx, ny, nm = (v[-1] for v in north)
        self.label(self.labels["z"], nx + 0.12, ny, nm)

        # Curved arrow above the pole, turning with the Earth (eastwards)
        spin = 360 * turn
        a = np.radians(np.linspace(spin, spin + ARROW_ARC, 200))
        arc = np.column_stack([ARROW_RADIUS * np.cos(a), ARROW_RADIUS * np.sin(a),
                               np.full_like(a, ARROW_HEIGHT)])
        polylines += self.arrow(*self.line(arc, LON_START))
        cx, cy, cm = project_xyz(np.array([[0.0, 0.0, ARROW_HEIGHT]]), LON_START, LAT0)
        self.label(self.omega, cx[0] + ARROW_RADIUS + 0.2, cy[0], 1.0)

        # x and y axes, turning with the Earth
        r = np.linspace(1.0, AXIS_LENGTH, 60)
        for name, lon in BODY_AXES:
            a = np.radians(lon)
            bx, by, bm = self.line(np.column_stack([r * np.cos(a), r * np.sin(a),
                                                    np.zeros_like(r)]), lon0)
            polylines += self.arrow(bx, by, bm)
            # Label just beyond the tip, along the axis, unless the Earth hides it
            ends = np.array([[np.cos(a), np.sin(a), 0.0]]) * np.array([[1.0], [AXIS_LENGTH]])
            ex, ey, _ = project_xyz(ends, lon0, LAT0)
            dx, dy = ex[1] - ex[0], ey[1] - ey[0]
            norm = max(np.hypot(dx, dy), 1e-6)
            self.label(self.labels[name], bx[-1] + 0.2 * dx / norm, by[-1] + 0.2 * dy / norm,
                       bm[-1])
        self.lines.draw(polylines)

        # Equator, dashed, slightly larger than the globe, fixed in space
        a = np.radians(np.linspace(0, 360, 400))
        ring = EQUATOR_RADIUS * np.column_stack([np.cos(a), np.sin(a), np.zeros_like(a)])
        self.equator.draw([self.line(ring, LON_START)])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", action="store_true", help="render one frame as PNG")
    args = parser.parse_args()

    OUTPUT.mkdir(exist_ok=True)
    globe = AxesGlobe()
    if args.preview:
        globe.frame(DURATION * 0.1)
        globe.fig.savefig(OUTPUT / "globe_axes.png", transparent=True)
        return
    render_transparent_video(globe.fig, globe.frame, DURATION, FPS,
                             OUTPUT / "globe_axes", matte=C9)


if __name__ == "__main__":
    main()
