"""Turning ASCII-art globe with a year of real earthquakes.

Earthquakes from the USGS catalogue (2025, M >= 6) light up when they
happen: a bright epicenter, a ring that grows with the magnitude and a fake
seismogram leaving the Earth's edge towards space, then a small mark that
stays.

Usage:
    uv run globe_seismes.py            # 30 s video in outputs/
    uv run globe_seismes.py --preview  # one PNG frame, fast
    uv run globe_seismes.py --fake     # synthetic catalogue instead of USGS
"""

import argparse

import numpy as np

from ascii_earth import (DURATION, LINE_WIDTH, MARK, MARK_FADING, MARK_FONTSIZE,
                         MARK_PAST, OUTPUT, ACCENT, GlyphLayer, HeroGlobe, orthographic_xy)
from seismes import (fake_catalogue, fake_seismogram, lifetime, ring_radius,
                     save_catalogue, select, small_circle, usgs_catalogue)

MIN_MAGNITUDE = 6.0  # earthquakes shown from the USGS catalogue
QUAKE_CHAR = "•"  # epicenters, during and after the earthquake
RING_ALPHA = (1.0, 0.0)  # opacity of rings and seismograms, at the start and the end
RING_FADE = 4  # the opacity stays high, then drops at the end (progress ** RING_FADE)
TRACE_WIDTH = LINE_WIDTH * 0.6
TRACE_GAP = 0.05  # between the Earth's edge and the start of a trace, Earth radii
TRACE_SPEED = 1.6  # the trace is fully recorded at this fraction of the lifetime


def trace_length(magnitude):
    return 0.35 + 0.25 * (magnitude - 6)


def trace_amplitude(magnitude):
    return 0.05 + 0.035 * (magnitude - 6)


class SeismicGlobe(HeroGlobe):
    """Turning ASCII-art globe with a year of real earthquakes."""

    name = "globe_seismes"
    preview = 0.55

    def __init__(self, fake=False, seed=42):
        super().__init__()
        if fake:
            self.catalogue = fake_catalogue(np.random.default_rng(seed), DURATION)
            save_catalogue(self.catalogue, OUTPUT / "catalogue_synthetique.csv")
        else:
            catalogue = usgs_catalogue(DURATION)
            self.catalogue = select(catalogue, catalogue["magnitude"] >= MIN_MAGNITUDE)
        self.seismograms = [fake_seismogram(i) for i in range(len(self.catalogue["time"]))]
        self.quakes = GlyphLayer(self.ax, MARK_FONTSIZE, zorder=3)
        self.lines = []  # pool of lines (rings and seismograms), reused frame to frame

    def line(self, k, width):
        while len(self.lines) <= k:
            self.lines.append(self.ax.plot([], [], color=ACCENT, solid_capstyle="round",
                                           solid_joinstyle="round", zorder=2.5)[0])
        self.lines[k].set_linewidth(width)
        return self.lines[k]

    def frame(self, t):
        lon0 = super().frame(t)
        cat = self.catalogue
        started = cat["time"] <= t
        age = t - cat["time"]
        active = started & (age < lifetime(cat["magnitude"]))
        past = started & ~active
        ex, ey, emu = orthographic_xy(cat["lat"], cat["lon"], lon0)
        seen = emu > 0

        marks = [(ex[past & seen], ey[past & seen], MARK_PAST)]
        n_lines = 0
        # Active earthquakes, smallest first so large ones end up on top
        for i in np.flatnonzero(active)[np.argsort(cat["magnitude"][active])]:
            magnitude = cat["magnitude"][i]
            progress = age[i] / lifetime(magnitude)
            alpha = RING_ALPHA[0] + progress ** RING_FADE * (RING_ALPHA[1] - RING_ALPHA[0])
            radius = ring_radius(magnitude) * np.sqrt(progress)
            if radius > 1:
                ring_lat, ring_lon = small_circle(cat["lat"][i], cat["lon"][i], radius, 180)
                rx, ry, rmu = orthographic_xy(np.r_[ring_lat, ring_lat[0]],
                                              np.r_[ring_lon, ring_lon[0]], lon0)
                ring = self.line(n_lines, LINE_WIDTH)
                ring.set_data(np.where(rmu > 0, rx, np.nan), np.where(rmu > 0, ry, np.nan))
                ring.set_alpha(alpha)
                n_lines += 1
            if not seen[i]:
                continue
            marks.append(([ex[i]], [ey[i]], MARK if progress < 0.5 else MARK_FADING))
            # Seismogram leaving the Earth's edge, in the earthquake's direction
            distance = np.hypot(ex[i], ey[i])
            if distance > 0.05:
                radial = np.array([ex[i], ey[i]]) / distance
                normal = np.array([-radial[1], radial[0]])
                u, signal = self.seismograms[i]
                shown = u <= min(1.0, progress * TRACE_SPEED)
                along = (1 + TRACE_GAP) + u[shown] * trace_length(magnitude)
                across = signal[shown] * trace_amplitude(magnitude)
                trace = self.line(n_lines, TRACE_WIDTH)
                trace.set_data(along * radial[0] + across * normal[0],
                               along * radial[1] + across * normal[1])
                trace.set_alpha(alpha)
                n_lines += 1

        x = np.concatenate([np.atleast_1d(m[0]) for m in marks])
        y = np.concatenate([np.atleast_1d(m[1]) for m in marks])
        style = np.concatenate([np.full(np.size(m[0]), m[2]) for m in marks])
        self.quakes.draw(x, y, np.full(len(x), QUAKE_CHAR), style)
        for line in self.lines[n_lines:]:
            line.set_data([], [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="synthetic catalogue")
    parser.add_argument("--seed", type=int, default=42)
    SeismicGlobe.main(parser)
