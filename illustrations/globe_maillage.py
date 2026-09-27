"""Turning ASCII-art globe inside a turning Delaunay mesh.

The animated version of the Objectifs illustration, for the home page hero:
the Earth makes one full turn during the video, and the mesh around it one
full turn the other way about a tilted axis, so the video loops. Same format
as globe_seismes.py (transparent, square), so the hero can show either.

Usage:
    uv run globe_maillage.py            # 30 s videos in outputs/
    uv run globe_maillage.py --preview  # one PNG frame, fast
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull

from ascii_earth import (
    ACCENT,
    C9,
    DepthLines,
    GlyphLayer,
    fibonacci_sphere,
    is_land,
    orthographic_xy,
    render_transparent_video,
)
from globe_seismes import (
    DPI,
    DURATION,
    FONTSIZE,
    WEIGHT,
    FPS,
    LAND,
    LAND_CHARS,
    LAT0,
    LON_START,
    EXTENT,
    N_POINTS,
    OCEAN,
    OCEAN_CHARS,
    OUTPUT,
    SIZE,
    STYLES,
    shade,
)

MESH_RADIUS = 1.7  # the mesh is a sphere around the Earth, in Earth radii
MESH_NODES = 24  # nodes spread uniformly over the mesh sphere
MESH_TILT = 20  # tilt of the mesh rotation axis, degrees
MESH_COLOR = ACCENT
MESH_WIDTH = 1.4 * 150 / DPI  # same width in pixels as the rings and orbits
MESH_BACK_ALPHA = 0.35  # opacity of the far side of the mesh


def rotation(axis_tilt, angle):
    """Rotation by `angle` about an axis tilted by `axis_tilt` from the pole."""
    a, t = np.radians(angle), np.radians(axis_tilt)
    spin = np.array(
        [[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]]
    )
    tilt = np.array(
        [[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]]
    )
    return tilt @ spin @ tilt.T


class MeshGlobe:
    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.lat, self.lon = fibonacci_sphere(N_POINTS)
        self.land = is_land(self.lat, self.lon)
        self.chars = np.where(
            self.land,
            rng.choice(list(LAND_CHARS), N_POINTS),
            rng.choice(list(OCEAN_CHARS), N_POINTS),
        )

        # Delaunay triangulation of the mesh sphere: the convex hull of its nodes
        lat, lon = np.radians(fibonacci_sphere(MESH_NODES))
        self.nodes = np.column_stack(
            [np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)]
        )
        hull = ConvexHull(self.nodes)
        edges = {
            tuple(sorted(e))
            for t in hull.simplices
            for e in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2]))
        }
        self.edges = np.array(sorted(edges))

        self.fig = plt.figure(figsize=(SIZE, SIZE), dpi=DPI)
        self.fig.patch.set_alpha(0)  # transparent: the website sets the color
        ax = self.fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(-EXTENT, EXTENT)
        ax.set_ylim(-EXTENT, EXTENT)
        ax.set_aspect("equal")
        ax.axis("off")
        # Characters keep their size relative to the Earth, as in the
        # seismic video
        self.surface = GlyphLayer(ax, STYLES, FONTSIZE, zorder=2, weight=WEIGHT)
        self.mesh = DepthLines(ax, MESH_COLOR, MESH_WIDTH, back=MESH_BACK_ALPHA)

    def frame(self, t):
        turn = t / DURATION
        lon0 = (LON_START - 360 * turn + 180) % 360 - 180

        # Surface
        x, y, mu = orthographic_xy(self.lat, self.lon, lon0, LAT0)
        front = mu > 0
        style = np.where(self.land, LAND, OCEAN) + shade(x, y, mu)
        self.surface.draw(x[front], y[front], self.chars[front], style[front])

        # Mesh, turning the other way about a tilted axis
        xyz = self.nodes @ rotation(MESH_TILT, 360 * turn).T
        lat = np.degrees(np.arcsin(np.clip(xyz[:, 2], -1, 1)))
        lon = np.degrees(np.arctan2(xyz[:, 1], xyz[:, 0]))
        mx, my, mmu = orthographic_xy(lat, lon, LON_START, LAT0)
        mx, my = MESH_RADIUS * mx, MESH_RADIUS * my

        # Each edge sampled along its length, so that its opacity follows the
        # depth; the Earth hides what passes behind it
        a, b = self.edges[:, 0], self.edges[:, 1]
        s = np.linspace(0, 1, 30)
        polylines = []
        for i, j in zip(a, b):
            px = mx[i] + s * (mx[j] - mx[i])
            py = my[i] + s * (my[j] - my[i])
            pm = mmu[i] + s * (mmu[j] - mmu[i])
            hidden = (pm < 0) & (np.hypot(px, py) < 1.03)
            polylines.append((np.where(hidden, np.nan, px), py, pm))
        self.mesh.draw(polylines)

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--preview", action="store_true", help="render one frame as PNG"
    )
    args = parser.parse_args()

    OUTPUT.mkdir(exist_ok=True)
    globe = MeshGlobe()
    if args.preview:
        globe.frame(DURATION * 0.2)
        globe.fig.savefig(OUTPUT / "globe_maillage.png", transparent=True)
        return
    render_transparent_video(
        globe.fig,
        globe.frame,
        DURATION,
        FPS,
        OUTPUT / "globe_maillage",
        matte=C9,
    )


if __name__ == "__main__":
    main()
