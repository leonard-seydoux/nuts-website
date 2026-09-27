"""Static ASCII-art illustrations for the sections of the home page.

- satellites.png: a small globe with satellite orbits around it (Contexte),
- terre_maillee.png: the globe of the satellites image inside a spherical
  Delaunay mesh (Objectifs),
- carte_workshops.png: round map of France with towns of the NuTS community
  (Workshops),
- reseau_pilotage.png: the labs of the steering committee, linked as a
  network (Pilotage).

All images are transparent PNGs: the website sets the background.

Usage:
    uv run sections.py
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import cartopy.io.shapereader as shapereader
import shapely
from shapely.prepared import prep

from matplotlib.collections import LineCollection
from scipy.spatial import ConvexHull

import globe_seismes as hero
from ascii_earth import (ACCENT, C0, C1, C3, C4, C6, C7, C8, C9, FONT, GlyphLayer,
                         fibonacci_sphere, is_land, orthographic_xy)

OUTPUT = Path(__file__).parent / "outputs" / "sections"
WIDTH, DPI = 6, 150  # inches, dots per inch: 900 px wide
FONTSIZE = 14
MAP_FONTSIZE = 18  # workshops map: fewer, bolder characters
N_POINTS = 2400  # surface points of the globes, as in the home page video

LAND_CHAR, OCEAN_CHAR = "#", "≈"


def canvas(xlim, ylim, width=WIDTH):
    """Transparent figure whose axes fill it, with equal aspect."""
    height = width * (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
    fig = plt.figure(figsize=(width, height), dpi=DPI)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def cell(ax, fontsize=FONTSIZE):
    """Width and height of a character cell, in data units."""
    points = ax.figure.get_figwidth() * 72
    per_point = (ax.get_xlim()[1] - ax.get_xlim()[0]) / points
    return 0.6 * fontsize * per_point, 1.2 * fontsize * per_point


def grid(ax, xlim, ylim, spacing=(1.25, 1.05), fontsize=FONTSIZE):
    """Points on a character grid, slightly looser than text."""
    width, height = cell(ax, fontsize)
    # Half a cell in from the edges, so that border characters are not cut
    x = np.arange(xlim[0] + width / 2, xlim[1] - width / 2, width * spacing[0])
    y = np.arange(ylim[0] + height / 2, ylim[1] - height / 2, height * spacing[1])
    x, y = np.meshgrid(x, y)
    return x.ravel(), y.ravel()




# Surface styles shared by the globes: ocean 0-2, land 3-5
SURFACE = hero.STYLES[:8]  # same look as the hero videos: ocean 0-3, land 4-7


def still_size(fontsize, extent):
    """Size of a hero-video character, for a still image framed at +/- extent
    Earth radii: same size relative to the Earth."""
    return fontsize * WIDTH / hero.SIZE * hero.EXTENT / extent


def globe_surface(lon0, lat0, n=N_POINTS):
    """Visible surface glyphs of a globe: x, y, chars, styles, mu."""
    lat, lon = fibonacci_sphere(n)
    land = is_land(lat, lon)
    x, y, mu = orthographic_xy(lat, lon, lon0, lat0)
    front = mu > 0
    chars = np.where(land, LAND_CHAR, OCEAN_CHAR)
    styles = np.where(land, 4, 0) + hero.shade(x, y, mu)
    return x[front], y[front], chars[front], styles[front], mu[front]


def save(fig, name):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    fig.savefig(path, transparent=True)
    plt.close(fig)
    print(f"saved {path}")


# ---------------------------------------------------------------------------
# Contexte: the Earth and satellite orbits
# ---------------------------------------------------------------------------

# Circular orbits: radius (Earth radii, not to scale), inclination, right
# ascension of the ascending node (degrees), satellite position along the
# orbit (degrees). Each orbit is drawn as the arc the satellite has just
# travelled (SAT_TRAIL).
ORBITS = [
    (1.25, 98, 30, 310),    # polar, low: Earth observation
    (1.45, 30, -60, 160),   # inclined, low
    (1.70, 55, 120, 200),   # inclined, medium: navigation
    (2.05, 0, 0, 130),      # equatorial, high: geostationary
]
SAT_LON0, SAT_LAT0 = 10, hero.LAT0  # same tilt as the hero videos
SAT_POINTS = hero.N_POINTS  # same symbols as the hero videos
SAT_EXTENT = 2.2
SAT_CHARS = "+*@&"  # one symbol per satellite, in the order of ORBITS
SAT_TRAIL = 270  # length of the orbit drawn behind each satellite, degrees
SAT_LINEWIDTH = 1.4  # orbits, in points (same as the rings of the globe video)
SAT_GAP = 0.15  # space on screen between an orbit and its satellite, in Earth radii


def orbit_xyz(radius, inclination, node, anomaly):
    """3D positions (Earth frame) on a circular orbit, anomaly in degrees."""
    u, i, o = np.radians(anomaly), np.radians(inclination), np.radians(node)
    x, y = np.cos(u), np.sin(u)
    x, y, z = x, y * np.cos(i), y * np.sin(i)
    x, y = x * np.cos(o) - y * np.sin(o), x * np.sin(o) + y * np.cos(o)
    return radius * np.stack([x, y, z], axis=-1)


def project_xyz(xyz, lon0, lat0):
    """Orthographic projection of 3D points: x, y, depth (> 0 towards us)."""
    r = np.linalg.norm(xyz, axis=-1)
    lat = np.degrees(np.arcsin(xyz[..., 2] / r))
    lon = np.degrees(np.arctan2(xyz[..., 1], xyz[..., 0]))
    x, y, mu = orthographic_xy(lat, lon, lon0, lat0)
    return r * x, r * y, r * mu


def satellites():
    fig, ax = canvas((-SAT_EXTENT, SAT_EXTENT), (-SAT_EXTENT, SAT_EXTENT))
    styles = SURFACE + [(ACCENT, 1.0)]
    globe = GlyphLayer(ax, styles, still_size(hero.FONTSIZE, SAT_EXTENT), zorder=2,
                       weight=hero.WEIGHT)
    sats = GlyphLayer(ax, styles, still_size(hero.MARK_FONTSIZE * 1.8, SAT_EXTENT),
                      zorder=4, weight="bold")

    x, y, chars, style, _ = globe_surface(SAT_LON0, SAT_LAT0, n=SAT_POINTS)
    globe.draw(x, y, chars, style)

    sat_x, sat_y, sat_chars, sat_styles = [], [], [], []
    for (radius, inclination, node, position), char in zip(ORBITS, SAT_CHARS):
        # Trail behind the satellite, as a solid line: the part hidden by the
        # Earth is left out, the part behind it passes under the globe
        anomaly = np.linspace(position - SAT_TRAIL, position, 600)
        ox, oy, depth = project_xyz(orbit_xyz(radius, inclination, node, anomaly),
                                    SAT_LON0, SAT_LAT0)
        hidden = (depth < 0) & (np.hypot(ox, oy) < 1.0)
        hidden |= np.hypot(ox - ox[-1], oy - oy[-1]) < SAT_GAP  # room for the satellite
        for in_front, zorder in ((False, 1), (True, 3)):
            keep = ~hidden & ((depth >= 0) == in_front)
            ax.plot(np.where(keep, ox, np.nan), np.where(keep, oy, np.nan),
                    color=ACCENT, linewidth=SAT_LINEWIDTH, solid_capstyle="round",
                    zorder=zorder)

        px, py, pdepth = project_xyz(orbit_xyz(radius, inclination, node, np.array([position])),
                                     SAT_LON0, SAT_LAT0)
        if not (pdepth[0] < 0 and np.hypot(px[0], py[0]) < 1.02):
            sat_x.append(px)
            sat_y.append(py)
            sat_chars.append([char])
            sat_styles.append([len(SURFACE)])

    sats.draw(np.concatenate(sat_x), np.concatenate(sat_y),
              np.concatenate(sat_chars), np.concatenate(sat_styles))
    save(fig, "satellites.png")


# ---------------------------------------------------------------------------
# Objectifs: the globe of the satellites image, under a Delaunay mesh
# ---------------------------------------------------------------------------

MESH_RADIUS = 1.7  # the mesh is a sphere around the Earth, in Earth radii
MESH_EXTENT = MESH_RADIUS * 1.05  # half-width of the view
MESH_NODES = 24  # nodes spread uniformly over the mesh sphere
MESH_BACK_ALPHA = 0.35  # opacity of the far side of the mesh


def terre_maillee():
    fig, ax = canvas((-MESH_EXTENT, MESH_EXTENT), (-MESH_EXTENT, MESH_EXTENT))
    # Same globe as the satellites image and the hero videos
    x, y, chars, style, _ = globe_surface(SAT_LON0, SAT_LAT0, n=SAT_POINTS)
    GlyphLayer(ax, SURFACE, still_size(hero.FONTSIZE, MESH_EXTENT), zorder=2,
               weight=hero.WEIGHT).draw(x, y, chars, style)

    # Delaunay triangulation of the mesh sphere: the convex hull of its nodes
    lat, lon = fibonacci_sphere(MESH_NODES)
    phi, lam = np.radians(lat), np.radians(lon)
    hull = ConvexHull(np.column_stack([np.cos(phi) * np.cos(lam),
                                       np.cos(phi) * np.sin(lam), np.sin(phi)]))
    edges = {tuple(sorted(e)) for t in hull.simplices for e in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2]))}
    edges = np.array(sorted(edges))
    mx, my, mu = orthographic_xy(lat, lon, SAT_LON0, SAT_LAT0)
    mx, my = MESH_RADIUS * mx, MESH_RADIUS * my
    segments = np.stack([np.column_stack([mx[edges[:, 0]], my[edges[:, 0]]]),
                         np.column_stack([mx[edges[:, 1]], my[edges[:, 1]]])], axis=1)
    front = mu[edges].mean(axis=1) > 0
    # Near side over the Earth
    ax.add_collection(LineCollection(segments[front], colors=C6, linewidths=SAT_LINEWIDTH,
                                     capstyle="round", zorder=3))
    # Far side: faint, and cut where the Earth hides it (the globe is made of
    # characters with gaps, so it cannot hide the lines by itself)
    t = np.linspace(0, 1, 60)[:, None]
    xs, ys = [], []
    for (x0, y0), (x1, y1) in segments[~front]:
        px, py = x0 + t[:, 0] * (x1 - x0), y0 + t[:, 0] * (y1 - y0)
        hidden = np.hypot(px, py) < 1.03
        xs += [np.where(hidden, np.nan, px), [np.nan]]
        ys += [np.where(hidden, np.nan, py), [np.nan]]
    ax.plot(np.concatenate(xs), np.concatenate(ys), color=C6, alpha=MESH_BACK_ALPHA,
            linewidth=SAT_LINEWIDTH, solid_capstyle="round", zorder=1)
    save(fig, "terre_maillee.png")


# ---------------------------------------------------------------------------
# Maps of France
# ---------------------------------------------------------------------------

LON_RANGE, LAT_RANGE = (-6.0, 10.5), (41.0, 51.6)
COS_LAT = np.cos(np.radians(46.3))  # equirectangular map, true scale at 46.3° N


def map_xy(lat, lon):
    return np.asarray(lon) * COS_LAT, np.asarray(lat)


def france():
    path = shapereader.natural_earth("50m", "cultural", "admin_0_countries")
    for record in shapereader.Reader(path).records():
        if record.attributes["ADMIN"] == "France":
            return prep(record.geometry)
    raise LookupError("France not found in Natural Earth")


def map_canvas():
    x0, y0 = map_xy(LAT_RANGE[0], LON_RANGE[0])
    x1, y1 = map_xy(LAT_RANGE[1], LON_RANGE[1])
    return canvas((x0, x1), (y0, y1))


# Round map: a disk centred on France, radius in map units (degrees of latitude)
DISK_CENTER, DISK_RADIUS = map_xy(46.4, 2.5), 6.5


def disk_canvas():
    """Square canvas around the round map, with characters of the same size
    as on the rectangular maps."""
    x0, _ = map_xy(LAT_RANGE[0], LON_RANGE[0])
    x1, _ = map_xy(LAT_RANGE[1], LON_RANGE[1])
    (cx, cy), r = DISK_CENTER, DISK_RADIUS * 1.1  # room for the edge characters
    return canvas((cx - r, cx + r), (cy - r, cy + r), width=WIDTH * 2 * r / (x1 - x0))


def france_glyphs(ax, char=LAND_CHAR):
    """Grid points inside mainland France and Corsica."""
    x, y = grid(ax, ax.get_xlim(), ax.get_ylim())
    inside = shapely.contains_xy(FRANCE.context, x / COS_LAT, y)
    return x[inside], y[inside], np.full(inside.sum(), char)


# Label placement per town: (dx, dy, horizontal alignment), in map units
PLACES = {
    "Paris": (0.0, 0.7, "center"),
    "Lyon": (0.35, 0.0, "left"),
    "Grenoble": (0.35, -0.1, "left"),
    "Strasbourg": (-0.2, -0.75, "center"),
    "Nancy": (0.0, 0.45, "center"),
    "Nantes": (-0.35, 0.0, "right"),
    "Rennes": (-0.35, 0.0, "right"),
    "Orléans": (0.0, -0.45, "center"),
    "Clermont-Ferrand": (-0.35, 0.0, "right"),
}


def label(ax, x, y, text, town):
    dx, dy, ha = PLACES[town]
    return ax.text(x + dx, y + dy, text, family=FONT, fontsize=12, color=C7,
                   ha=ha, va="center", ma="center", parse_math=False,
                   fontweight="bold", linespacing=1.1)


def outside_labels(ax, labels, x, y, margin=0.15):
    """Mask of the points (x, y) that no label covers."""
    ax.figure.canvas.draw()
    keep = np.ones(len(x), bool)
    to_data = ax.transData.inverted()
    for text in labels:
        (x0, y0), (x1, y1) = to_data.transform(text.get_window_extent().get_points())
        keep &= ~((x > x0 - margin) & (x < x1 + margin) & (y > y0 - margin) & (y < y1 + margin))
    return keep


# Towns marked on the workshops map: town, lat, lon
WORKSHOP_TOWNS = [
    ("Paris", 48.85, 2.35),
    ("Lyon", 45.76, 4.83),
    ("Strasbourg", 48.58, 7.75),
    ("Nantes", 47.22, -1.55),
    ("Grenoble", 45.19, 5.72),
    ("Toulouse", 43.60, 1.44),
    ("Marseille", 43.30, 5.37),
    ("Rennes", 48.11, -1.68),
    ("Bordeaux", 44.84, -0.58),
    ("Pau", 43.30, -0.37),
    ("Orléans", 47.90, 1.90),
    ("Clermont-Ferrand", 45.78, 3.08),
]


def dotted_path(ax, points):
    """Points every character width along a polyline."""
    width, _ = cell(ax)
    xs, ys = [], []
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
        n = max(int(np.hypot(x1 - x0, y1 - y0) / (width * 1.6)), 1)
        t = np.linspace(0, 1, n, endpoint=False)[1:]
        xs.append(x0 + t * (x1 - x0))
        ys.append(y0 + t * (y1 - y0))
    return np.concatenate(xs), np.concatenate(ys)


def carte_workshops():
    fig, ax = disk_canvas()
    # France, neighbouring countries, sea, towns
    styles = [(C8, 0.85), (C8, 0.3), (C9, 0.5), (C3, 1.0)]
    towns = np.array([map_xy(lat, lon) for _, lat, lon in WORKSHOP_TOWNS])

    x, y = grid(ax, ax.get_xlim(), ax.get_ylim(), fontsize=MAP_FONTSIZE)
    disk = np.hypot(x - DISK_CENTER[0], y - DISK_CENTER[1]) <= DISK_RADIUS
    x, y = x[disk], y[disk]
    lon, lat = x / COS_LAT, y
    in_france = shapely.contains_xy(FRANCE.context, lon, lat)
    land = is_land(lat, lon)
    chars = np.where(land | in_france, LAND_CHAR, OCEAN_CHAR)
    style = np.where(in_france, 0, np.where(land, 1, 2))

    # Each town replaces the closest character of France
    candidates = np.flatnonzero(in_france)
    distance = np.hypot(x[candidates, None] - towns[:, 0], y[candidates, None] - towns[:, 1])
    closest = candidates[np.argmin(distance, axis=0)]
    chars[closest] = "@"
    style[closest] = 3
    GlyphLayer(ax, styles, MAP_FONTSIZE, weight="bold").draw(x, y, chars, style)

    save(fig, "carte_workshops.png")


# Labs of the steering committee: town, lat, lon, members
LABS = [
    ("Grenoble", 45.19, 5.72, 4),
    ("Paris", 48.85, 2.35, 3),
    ("Nantes", 47.22, -1.55, 2),
    ("Nancy", 48.69, 6.18, 2),
    ("Strasbourg", 48.58, 7.75, 2),
    ("Rennes", 48.11, -1.68, 1),
    ("Orléans", 47.90, 1.90, 1),
    ("Clermont-Ferrand", 45.78, 3.08, 1),
]


def reseau_pilotage():
    fig, ax = map_canvas()
    styles = [(C8, 0.35), (C0, 0.8), (C1, 1.0)]
    nodes = np.array([map_xy(lat, lon) for _, lat, lon, _ in LABS])

    labels = [label(ax, nx, ny, town, town) for (town, *_), (nx, ny) in zip(LABS, nodes)]

    x, y, chars = france_glyphs(ax)
    free = outside_labels(ax, labels, x, y)
    GlyphLayer(ax, styles, FONTSIZE, zorder=1).draw(
        x[free], y[free], chars[free], np.zeros(free.sum(), int))

    lx, ly = [], []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            px, py = dotted_path(ax, nodes[[i, j]])
            lx.append(px)
            ly.append(py)
    lx, ly = np.concatenate(lx), np.concatenate(ly)
    free = outside_labels(ax, labels, lx, ly, margin=0.05)
    lx, ly = lx[free], ly[free]
    GlyphLayer(ax, styles, FONTSIZE, zorder=2).draw(
        lx, ly, np.full(len(lx), "·"), np.full(len(lx), 1))

    for (town, lat, lon, members), (nx, ny) in zip(LABS, nodes):
        size = FONTSIZE * (1.1 + 0.45 * members)
        GlyphLayer(ax, styles, size, zorder=3).draw([nx], [ny], ["@"], [2])
    save(fig, "reseau_pilotage.png")


FRANCE = france()

if __name__ == "__main__":
    satellites()
    terre_maillee()
    carte_workshops()
    reseau_pilotage()
