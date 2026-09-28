"""NuTS logo, with the colors and the font of the illustrations.

A cyan ≈ and an olive # (DejaVu Sans Mono, bold), the two characters of the
illustrations, side by side inside a pink hazelnut (a nod to the name of the
network) tilted so that its point faces the bottom right, on a transparent
background. One design, two sets of colors:

- logo_icon.svg/.png: the matplotlib colors, for the dark theme; the PNG is
  also the favicon (copied as docs/images/logo/favicon.png) (they stand out on dark and blue backgrounds),
- logo_icon_light.svg: darker shades, for the header of the light theme,
  where a plain olive # would vanish on the olive bar.

Usage:
    uv run logo.py
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Same SVG for the same logo (no random ids), so that git only sees real changes
plt.rcParams["svg.hashsalt"] = "nuts"
from matplotlib.colors import to_hex, to_rgb
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

from ascii_earth import ACCENT, C8, C9, FONT

OUTPUT = Path(__file__).parent / "outputs" / "logo"


def blend(color, amount, base="white"):
    """Opaque mix of `color` (share `amount`) with `base`."""
    return to_hex(
        amount * np.array(to_rgb(color))
        + (1 - amount) * np.array(to_rgb(base))
    )


BOLD = FontProperties(family=FONT, weight="bold")
LINE_WIDTH = 0.1  # pink outline, in units of the nut's half-width
TILT = -135  # the nut is turned so that its point faces the bottom right (degrees)
# NuTS written inside, reading from the bottom left to the top right:
# (text, width in nut half-widths, centre in the frame of the upright nut)
WORD = ("NuTS", 1.25, (0.0, -0.08))
WORD_ANGLE = 45  # degrees
WORD_WEIGHT = 0.035  # outline added around each letter, extra bold (nut half-widths)
# Colors of the letters of NuTS, per file: the u in olive, N, T and S in cyan;
# darker shades for the light theme, readable on the olive bar
COLORS = {
    "logo_icon": {"u": C8, "other": C9},
    "logo_icon_light": {"u": blend(C8, 0.7, "black"), "other": blend(C9, 0.8, "black")},
}
MARGIN = 0.08


def word(ax, text, width, center, angle, colors, points=0):
    """`text`, `width` wide, centred on `center` (frame of the upright nut)
    and turned by `angle` degrees; each letter colored from `colors`."""
    whole = TextPath((0, 0), text, size=1, prop=BOLD)
    box = whole.get_extents()
    scale = width / box.width
    x, y = tilted(*center)
    move = (Affine2D()
            .translate(-box.x0 - box.width / 2, -box.y0 - box.height / 2)
            .scale(scale)
            .rotate_deg(angle)
            .translate(x, y))
    # Monospace font: letter k starts k advances after the first one
    advance = TextPath((0, 0), "MM", size=1, prop=BOLD).get_extents().width \
        - TextPath((0, 0), "M", size=1, prop=BOLD).get_extents().width
    for k, letter in enumerate(text):
        path = TextPath((k * advance, 0), letter, size=1, prop=BOLD).transformed(move)
        color = colors.get(letter, colors["other"])
        ax.add_patch(PathPatch(path, facecolor=color, edgecolor=color,
                               linewidth=WORD_WEIGHT * points, joinstyle="round"))


def hazelnut(n=400, point=0.28):
    """Outline of a hazelnut: round at the bottom, closing in to a soft point
    at the top (the smaller `point`, the sharper it is). Half-width 1."""
    t = np.linspace(0, 2 * np.pi, n)
    x = np.sin(t) * np.abs(np.sin(t / 2)) ** point
    y = np.cos(t)
    return x / np.abs(x).max(), 1.06 * y


def hilum(level=-0.62, sag=0.1):
    """The paler base of the nut: an arc across its bottom, from one side of
    the outline to the other at height `level`, sagging by `sag`."""
    x, y = hazelnut()
    lower = y < 0
    half = np.interp(
        level,
        np.sort(y[lower & (x > 0)]),
        x[lower & (x > 0)][np.argsort(y[lower & (x > 0)])],
    )
    u = np.linspace(-half, half, 100)
    return u, level - sag * (1 - (u / half) ** 2)


def tilted(x, y):
    c, s = np.cos(np.radians(TILT)), np.sin(np.radians(TILT))
    return c * x - s * y, s * x + c * y


def icon(name, colors):
    curves = [tilted(*hazelnut()), tilted(*hilum())]
    # Square frame around the tilted nut, centred on it
    x, y = np.concatenate([c[0] for c in curves]), np.concatenate([c[1] for c in curves])
    cx, cy = (x.min() + x.max()) / 2, (y.min() + y.max()) / 2
    half = max(x.max() - x.min(), y.max() - y.min()) / 2 + LINE_WIDTH / 2 + MARGIN
    fig = plt.figure(figsize=(2, 2), dpi=200)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
    ax.set_aspect("equal")
    ax.axis("off")

    # Pink outline of the nut and its base, as strokes of LINE_WIDTH
    points = fig.get_figheight() * 72 / (2 * half)  # points per unit
    for x, y in curves:
        ax.plot(
            x,
            y,
            color=ACCENT,
            linewidth=LINE_WIDTH * points,
            solid_capstyle="round",
            solid_joinstyle="round",
        )
    word(ax, WORD[0], WORD[1], WORD[2], WORD_ANGLE, colors, points)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "png"):
        fig.savefig(OUTPUT / f"{name}.{ext}", transparent=True, metadata={"Date": None})
    plt.close(fig)
    print(f"saved {OUTPUT}/{name}.svg/.png")


if __name__ == "__main__":
    for name, colors in COLORS.items():
        icon(name, colors)
