"""Turning ASCII-art globe with a sketch of its rotation.

The rotation axis z goes through the poles and out of the globe; a curved
arrow labelled Omega turns with the Earth above the North Pole; the x and y
axes, in the equatorial plane (towards 0 and 90 degrees East), turn with the
Earth; the equator is a dashed circle fixed in space.

Usage:
    uv run globe_axes.py            # 30 s videos in outputs/
    uv run globe_axes.py --preview  # one PNG frame, fast
"""

import numpy as np

from ascii_earth import (ACCENT, DURATION, LON_START, MARK_FONTSIZE, DepthLines,
                         HeroGlobe, depth_alpha, project_line, project_xyz)

AXIS_LENGTH = 1.75  # the axis sticks out of the globe up to this radius
ARROW_HEIGHT, ARROW_RADIUS = 1.38, 0.32  # curved arrow around the axis, above the pole
ARROW_ARC = 270  # degrees
EQUATOR_RADIUS = 1.2  # dashed equator, fixed in space
BODY_AXES = [("x", 0), ("y", 90)]  # axes turning with the Earth: label, longitude
HEAD = 0.09  # arrowhead length, in Earth radii
LABEL_SIZE = MARK_FONTSIZE * 2.2


def arrow(x, y, mu):
    """A line and the two strokes of its arrowhead, shaded by the depth of the tip."""
    polylines = [(x, y, mu)]
    if np.isfinite(x[-1]):
        d = np.array([x[-1] - x[-2], y[-1] - y[-2]])
        d /= np.linalg.norm(d)
        for side in (1, -1):
            c, s = np.cos(np.radians(150 * side)), np.sin(np.radians(150 * side))
            wing = HEAD * np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
            polylines.append((np.array([x[-1], x[-1] + wing[0]]),
                              np.array([y[-1], y[-1] + wing[1]]), np.full(2, mu[-1])))
    return polylines


def radial(direction, start=1.0, stop=AXIS_LENGTH, n=60):
    """Points along a line from the centre, between two radii."""
    return np.linspace(start, stop, n)[:, None] * np.asarray(direction, float)


class AxesGlobe(HeroGlobe):
    """Turning ASCII-art globe with a sketch of its rotation."""

    name = "globe_axes"
    preview = 0.1

    def __init__(self):
        super().__init__()
        self.lines = DepthLines(self.ax)
        self.equator = DepthLines(self.ax, dash=0.1)
        style = dict(color=ACCENT, fontsize=LABEL_SIZE, ha="center", va="center", zorder=4)
        self.labels = {name: self.ax.text(0, 0, f"${name}$", **style)
                       for name in ["z", r"\Omega"] + [name for name, _ in BODY_AXES]}

    def label(self, name, x, y, mu):
        text = self.labels[name]
        text.set_position((x, y))
        text.set_visible(bool(np.isfinite(x)))
        text.set_alpha(float(depth_alpha(mu)))

    def frame(self, t):
        lon0 = super().frame(t)
        turn = t / DURATION

        # Rotation axis z, out of the globe on both sides (inside, the Earth hides it)
        north = project_line(radial([0, 0, 1]), LON_START)
        south = project_line(radial([0, 0, -1]), LON_START)
        polylines = arrow(*north) + [south]
        self.label("z", north[0][-1] + 0.12, north[1][-1], north[2][-1])

        # Curved arrow above the pole, turning with the Earth (eastwards)
        a = np.radians(np.linspace(360 * turn, 360 * turn + ARROW_ARC, 200))
        arc = np.column_stack([ARROW_RADIUS * np.cos(a), ARROW_RADIUS * np.sin(a),
                               np.full_like(a, ARROW_HEIGHT)])
        polylines += arrow(*project_line(arc, LON_START))
        cx, cy, _ = project_xyz(np.array([[0.0, 0.0, ARROW_HEIGHT]]), LON_START)
        self.label(r"\Omega", cx[0] + ARROW_RADIUS + 0.2, cy[0], 1.0)

        # x and y axes, turning with the Earth
        for name, lon in BODY_AXES:
            direction = [np.cos(np.radians(lon)), np.sin(np.radians(lon)), 0.0]
            bx, by, bm = project_line(radial(direction), lon0)
            polylines += arrow(bx, by, bm)
            # Label just beyond the tip, along the axis, unless the Earth hides it
            ex, ey, _ = project_xyz(radial(direction, n=2), lon0)
            dx, dy = ex[1] - ex[0], ey[1] - ey[0]
            norm = max(np.hypot(dx, dy), 1e-6)
            self.label(name, bx[-1] + 0.2 * dx / norm, by[-1] + 0.2 * dy / norm, bm[-1])
        self.lines.draw(polylines)

        # Equator, dashed, slightly larger than the globe, fixed in space
        a = np.radians(np.linspace(0, 360, 400))
        ring = EQUATOR_RADIUS * np.column_stack([np.cos(a), np.sin(a), np.zeros_like(a)])
        self.equator.draw([project_line(ring, LON_START)])


if __name__ == "__main__":
    AxesGlobe.main()
