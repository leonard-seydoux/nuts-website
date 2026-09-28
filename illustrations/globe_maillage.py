"""Turning ASCII-art globe inside a turning Delaunay mesh.

The Earth makes one full turn during the video, and the mesh around it one
full turn the other way about a tilted axis, so the video loops.

Usage:
    uv run globe_maillage.py            # 30 s videos in outputs/
    uv run globe_maillage.py --preview  # one PNG frame, fast
"""

import numpy as np
from scipy.spatial import ConvexHull

from ascii_earth import (DURATION, LON_START, DepthLines, HeroGlobe, fibonacci_sphere,
                         orthographic_xy)

MESH_RADIUS = 1.7  # the mesh is a sphere around the Earth, in Earth radii
MESH_NODES = 24  # nodes spread uniformly over the mesh sphere
MESH_TILT = 20  # tilt of the mesh rotation axis, degrees


def rotation(axis_tilt, angle):
    """Rotation by `angle` about an axis tilted by `axis_tilt` from the pole."""
    a, t = np.radians(angle), np.radians(axis_tilt)
    spin = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    tilt = np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])
    return tilt @ spin @ tilt.T


class MeshGlobe(HeroGlobe):
    """Turning ASCII-art globe inside a turning Delaunay mesh."""

    name = "globe_maillage"
    preview = 0.2

    def __init__(self):
        super().__init__()
        # Delaunay triangulation of the mesh sphere: the convex hull of its nodes
        lat, lon = np.radians(fibonacci_sphere(MESH_NODES))
        self.nodes = np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon),
                                      np.sin(lat)])
        edges = {tuple(sorted(e)) for t in ConvexHull(self.nodes).simplices
                 for e in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2]))}
        self.edges = np.array(sorted(edges))
        self.mesh = DepthLines(self.ax)

    def frame(self, t):
        super().frame(t)
        # Mesh, turning the other way about a tilted axis
        xyz = self.nodes @ rotation(MESH_TILT, 360 * t / DURATION).T
        lat = np.degrees(np.arcsin(np.clip(xyz[:, 2], -1, 1)))
        lon = np.degrees(np.arctan2(xyz[:, 1], xyz[:, 0]))
        mx, my, mmu = orthographic_xy(lat, lon, LON_START)
        mx, my = MESH_RADIUS * mx, MESH_RADIUS * my

        # Each edge sampled along its length, so that its opacity follows the
        # depth; the Earth hides what passes behind it
        s = np.linspace(0, 1, 30)
        polylines = []
        for i, j in self.edges:
            px, py = mx[i] + s * (mx[j] - mx[i]), my[i] + s * (my[j] - my[i])
            pm = mmu[i] + s * (mmu[j] - mmu[i])
            hidden = (pm < 0) & (np.hypot(px, py) < 1.03)
            polylines.append((np.where(hidden, np.nan, px), py, pm))
        self.mesh.draw(polylines)


if __name__ == "__main__":
    MeshGlobe.main()
