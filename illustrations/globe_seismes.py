"""Turning ASCII-art globe with a year of real earthquakes.

The surface is a set of points spread uniformly on the sphere, each with a
fixed character, so the characters travel with the globe as it turns. The
globe is tilted to show the North Pole and makes one full turn during the
video, so the video loops.

Earthquakes from the USGS catalogue (2025, M >= 6) light up when they
happen: a bright epicenter and a ring that grows with the magnitude, then a
small mark that stays.

Usage:
    uv run globe_seismes.py            # 30 s video in outputs/
    uv run globe_seismes.py --preview  # one PNG frame, fast
    uv run globe_seismes.py --fake     # synthetic catalogue instead of USGS
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import PathCollection
from matplotlib.patches import Circle
from matplotlib.transforms import Affine2D
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.path import shapely_to_path
from shapely.ops import unary_union

from ascii_earth import (ACCENT, C0, C8, C9, GlyphLayer,
                         fibonacci_sphere, is_land, orthographic_xy, render_transparent_video)
from seismes import (fake_catalogue, lifetime, ring_radius, save_catalogue,
                     small_circle, usgs_catalogue)

SIZE, DPI = 8.4, 105  # square figure, in inches: about 880 x 880 px
# Framing shared by all the hero videos (globe_*.py), so that the Earth is
# the same in all of them: same size, centred, same view, same characters
EXTENT = 2.25  # half-width of the view, in Earth radii: room for the satellites
FONTSIZE = 1.45 * 23 * 1.05 / EXTENT  # large and bold: legible on light backgrounds
WEIGHT = "bold"
MARK_FONTSIZE = 23 * 1.05 / EXTENT  # earthquake dots and satellites
N_POINTS = 900  # surface points over the whole sphere
DISK = None  # color of a disk behind the globe (e.g. "#e6e6e6"), or None
# Basemap under the characters: Natural Earth 1:110m, light tints
BASEMAP = False  # Natural Earth continents and ocean tint under the characters
BASEMAP_OCEAN = (C9, 0.28)
BASEMAP_LAND = (C0, 0.40)
LAT0 = -4  # latitude facing the viewer: seen from just below the equator
LON_START = 150  # longitude facing the viewer at t = 0 (Pacific)
DURATION = 30  # seconds, one full turn
FPS = 24
MIN_MAGNITUDE = 6.0  # earthquakes shown from the USGS catalogue
OUTPUT = Path(__file__).parent / "outputs"

LAND_CHARS = "#"
OCEAN_CHARS = "≈"
QUAKE_CHAR = "•"  # epicenters, during and after the earthquake

# Glyph styles: (color, alpha). Ocean and land have three shades, from the
# center of the globe to its edge.
STYLES = [
    (C9, 0.95), (C9, 0.80), (C9, 0.60), (C9, 0.35),  # 0-3 ocean, day to night
    (C8, 1.00), (C8, 0.90), (C8, 0.70), (C8, 0.40),  # 4-7 land, day to night
    (ACCENT, 1.00),  # 8 epicenter, fresh
    (ACCENT, 0.60),  # 9 epicenter, fading
    (ACCENT, 0.55),  # 10 past earthquake
]
# Rings are solid lines, fainter as they grow
RING_COLOR = ACCENT
# Same width in pixels as the orbits of the satellites image (1.4 pt at 150 dpi,
# on an image of about the same size)
RING_WIDTH = 1.4 * 150 / DPI
RING_ALPHA = (1.0, 0.0)  # opacity at the start and at the end
RING_FADE = 4  # the opacity stays high, then drops at the end (progress ** RING_FADE)
# Fake seismograms leaving the Earth's edge towards space, in the direction of
# each visible earthquake: length and amplitude grow with the magnitude
TRACE_WIDTH = RING_WIDTH * 0.6
TRACE_GAP = 0.05  # between the Earth's edge and the start of a trace, Earth radii
TRACE_SPEED = 1.6  # the trace is fully recorded at this fraction of the lifetime


def trace_length(magnitude):
    return 0.35 + 0.25 * (magnitude - 6)


def trace_amplitude(magnitude):
    return 0.05 + 0.035 * (magnitude - 6)


def fake_seismogram(seed, n=400):
    """A seismogram-like signal along u in [0, 1], peak amplitude 1: noise, a
    small P arrival, a larger S arrival and a decaying coda."""
    rng = np.random.default_rng(seed)
    u = np.linspace(0, 1, n)
    noise = np.convolve(rng.normal(size=n), np.ones(8) / 8, mode="same") * 0.12

    def arrival(onset, amplitude, frequency, decay):
        after = np.clip(u - onset, 0, None)
        envelope = np.where(u > onset, np.exp(-after / decay) * (1 - np.exp(-after / 0.01)), 0)
        return amplitude * envelope * np.sin(2 * np.pi * frequency * after + rng.uniform(0, 6.3))

    p_onset = rng.uniform(0.08, 0.15)
    s_onset = p_onset + rng.uniform(0.15, 0.25)
    signal = (noise + arrival(p_onset, 0.35, rng.uniform(16, 20), 0.06)
              + arrival(s_onset, 1.0, rng.uniform(10, 13), 0.18))
    return u, signal / np.abs(signal).max()
OCEAN, LAND = 0, 4
EPI, EPI_FADE, PAST = range(8, 11)


def select(catalogue, keep):
    """Subset of a catalogue."""
    return {key: np.asarray(value)[keep] if key != "date" else
            [d for d, k in zip(value, keep) if k] for key, value in catalogue.items()}


# Direction of the (fake) Sun in the viewer's frame (x right, y up, z towards
# the viewer): from the front left, so the night side is on the right
SUN = np.array([-0.75, 0.25, 0.6]) / np.linalg.norm([-0.75, 0.25, 0.6])


def shade(x, y, mu):
    """Shade index (0 lit, 3 night) of visible points (x, y, mu) of the sphere."""
    light = SUN[0] * x + SUN[1] * y + SUN[2] * mu
    return np.where(light > 0.55, 0, np.where(light > 0.2, 1, np.where(light > -0.05, 2, 3)))


class Basemap:
    """Natural Earth land polygons, projected on the unit disk by cartopy."""

    def __init__(self, ax, zorder):
        self.land = unary_union(list(cfeature.LAND.with_scale("110m").geometries()))
        color, alpha = BASEMAP_LAND
        self.collection = PathCollection([], facecolors=color, alpha=alpha,
                                         edgecolors="none", zorder=zorder)
        ax.add_collection(self.collection, autolim=False)
        self.ax = ax

    def draw(self, lon0, lat0):
        projection = ccrs.Orthographic(lon0, lat0)
        land = projection.project_geometry(self.land, ccrs.PlateCarree())
        radius = projection.globe.semimajor_axis
        self.collection.set_paths([shapely_to_path(land)])
        self.collection.set_transform(Affine2D().scale(1 / radius) + self.ax.transData)


class Globe:
    def __init__(self, catalogue, seed=0):
        self.catalogue = catalogue

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
        if DISK:
            ax.add_patch(Circle((0, 0), 1.0, facecolor=DISK, edgecolor="none", zorder=0))
        self.basemap = None
        if BASEMAP:
            color, alpha = BASEMAP_OCEAN
            ax.add_patch(Circle((0, 0), 1.0, facecolor=color, alpha=alpha,
                                edgecolor="none", zorder=0.1))
            self.basemap = Basemap(ax, zorder=0.2)
        self.surface = GlyphLayer(ax, STYLES, FONTSIZE, zorder=1, weight=WEIGHT)
        self.quakes = GlyphLayer(ax, STYLES, MARK_FONTSIZE, zorder=2)
        self.ax = ax
        self.rings = []  # pool of lines, reused from frame to frame
        self.traces = []  # same, for the seismograms
        self.seismograms = [fake_seismogram(i) for i in range(len(catalogue["time"]))]

    def ring_line(self, k):
        while len(self.rings) <= k:
            line, = self.ax.plot([], [], color=RING_COLOR, linewidth=RING_WIDTH,
                                 solid_capstyle="round", zorder=1.5)
            self.rings.append(line)
        return self.rings[k]

    def trace_line(self, k):
        while len(self.traces) <= k:
            line, = self.ax.plot([], [], color=RING_COLOR, linewidth=TRACE_WIDTH,
                                 solid_capstyle="round", solid_joinstyle="round", zorder=1.5)
            self.traces.append(line)
        return self.traces[k]

    def frame(self, t):
        cat = self.catalogue
        lon0 = (LON_START - 360 * t / DURATION + 180) % 360 - 180

        # Surface
        if self.basemap:
            self.basemap.draw(lon0, LAT0)
        x, y, mu = orthographic_xy(self.lat, self.lon, lon0, LAT0)
        front = mu > 0
        style = np.where(self.land, LAND, OCEAN) + shade(x, y, mu)
        self.surface.draw(x[front], y[front], self.chars[front], style[front])

        # Earthquakes
        started = cat["time"] <= t
        age = t - cat["time"]
        active = started & (age < lifetime(cat["magnitude"]))
        past = started & ~active
        ex, ey, emu = orthographic_xy(cat["lat"], cat["lon"], lon0, LAT0)
        seen = emu > 0

        xs, ys, chars, styles = [], [], [], []

        def add(x, y, char, style):
            xs.append(np.atleast_1d(x))
            ys.append(np.atleast_1d(y))
            chars.append(np.full(np.size(x), char))
            styles.append(np.full(np.size(x), style))

        add(ex[past & seen], ey[past & seen], QUAKE_CHAR, PAST)

        # Active earthquakes, smallest first so large ones end up on top
        n_rings = n_traces = 0
        for i in np.flatnonzero(active)[np.argsort(cat["magnitude"][active])]:
            progress = age[i] / lifetime(cat["magnitude"][i])
            fresh = progress < 0.5
            radius = ring_radius(cat["magnitude"][i]) * np.sqrt(progress)
            if radius > 1:
                ring_lat, ring_lon = small_circle(cat["lat"][i], cat["lon"][i], radius, 180)
                ring_lat, ring_lon = np.r_[ring_lat, ring_lat[0]], np.r_[ring_lon, ring_lon[0]]
                rx, ry, rmu = orthographic_xy(ring_lat, ring_lon, lon0, LAT0)
                line = self.ring_line(n_rings)
                line.set_data(np.where(rmu > 0, rx, np.nan), np.where(rmu > 0, ry, np.nan))
                fade = progress ** RING_FADE
                line.set_alpha(RING_ALPHA[0] + fade * (RING_ALPHA[1] - RING_ALPHA[0]))
                n_rings += 1
            if seen[i]:
                add(ex[i], ey[i], QUAKE_CHAR, EPI if fresh else EPI_FADE)
                # Seismogram leaving the Earth's edge, in the earthquake's direction
                distance = np.hypot(ex[i], ey[i])
                if distance > 0.05:
                    radial = np.array([ex[i], ey[i]]) / distance
                    normal = np.array([-radial[1], radial[0]])
                    u, signal = self.seismograms[i]
                    shown = u <= min(1.0, progress * TRACE_SPEED)
                    along = (1 + TRACE_GAP) + u[shown] * trace_length(cat["magnitude"][i])
                    across = signal[shown] * trace_amplitude(cat["magnitude"][i])
                    line = self.trace_line(n_traces)
                    line.set_data(along * radial[0] + across * normal[0],
                                  along * radial[1] + across * normal[1])
                    fade = progress ** RING_FADE
                    line.set_alpha(RING_ALPHA[0] + fade * (RING_ALPHA[1] - RING_ALPHA[0]))
                    n_traces += 1

        self.quakes.draw(np.concatenate(xs), np.concatenate(ys),
                         np.concatenate(chars), np.concatenate(styles))
        for line in self.rings[n_rings:] + self.traces[n_traces:]:
            line.set_data([], [])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", action="store_true", help="render one frame as PNG")
    parser.add_argument("--fake", action="store_true", help="synthetic catalogue")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUTPUT.mkdir(exist_ok=True)
    if args.fake:
        catalogue = fake_catalogue(np.random.default_rng(args.seed), DURATION)
        save_catalogue(catalogue, OUTPUT / "catalogue_synthetique.csv")
    else:
        catalogue = usgs_catalogue(DURATION)
        catalogue = select(catalogue, catalogue["magnitude"] >= MIN_MAGNITUDE)
    globe = Globe(catalogue)
    fig = globe.fig

    if args.preview:
        globe.frame(DURATION * 0.55)
        fig.savefig(OUTPUT / "globe_seismes.png", transparent=True)
        return

    # Invisible pixels take the color of the globe's edge (or of the ocean
    # characters, without a disk), so that whatever the codecs bleed out of
    # them blends with the globe
    edge = DISK or C9
    if BASEMAP and DISK:
        edge = matplotlib.colors.to_hex(
            BASEMAP_OCEAN[1] * np.array(matplotlib.colors.to_rgb(BASEMAP_OCEAN[0]))
            + (1 - BASEMAP_OCEAN[1]) * np.array(matplotlib.colors.to_rgb(DISK)))
    render_transparent_video(fig, globe.frame, DURATION, FPS, OUTPUT / "globe_seismes",
                             matte=edge)


if __name__ == "__main__":
    main()
