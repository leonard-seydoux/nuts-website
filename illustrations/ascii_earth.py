"""ASCII-art Earth rendered with matplotlib, in the NuTS graphic style.

Everything the globe videos (globe_*.py) share lives here: the palette, the
framing, the turning Earth made of characters (HeroGlobe), the lines and
glyphs drawn around it, and the rendering of transparent videos for the web.
Each globe_*.py only adds what it draws around the Earth.

Characters are drawn as vector glyphs: each (character, style) pair is one
matplotlib PathCollection whose positions change from frame to frame
(GlyphLayer). This draws thousands of characters in a few milliseconds.
"""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")  # off-screen rendering, same pixel sizes on every screen
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection, PathCollection  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402
from global_land_mask import globe  # noqa: E402

# Matplotlib default palette (tab10), shared with the website
C0, C1, C2, C3, C4 = "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"
C5, C6, C7, C8, C9 = "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
OCEAN_COLOR, LAND_COLOR = C9, C8
ACCENT = C6  # earthquakes, satellites, meshes, axes, field lines

FONT = "DejaVu Sans Mono"
ADVANCE = 1233 / 2048  # character width of DejaVu Sans Mono, in em

# ffmpeg executable: $FFMPEG, else Homebrew's (recent enough for HEVC with
# alpha), else the first one on the PATH
FFMPEG = (
    os.environ.get("FFMPEG")
    or shutil.which("ffmpeg", path="/opt/homebrew/bin")
    or "ffmpeg"
)

OUTPUT = Path(__file__).parent / "outputs"


# ---------------------------------------------------------------------------
# Framing, shared by all the videos: same Earth, same size, same view
# ---------------------------------------------------------------------------

SIZE, DPI = 8.4, 105  # square figure, in inches: about 880 x 880 px
EXTENT = 2.25  # half-width of the view, in Earth radii: room around the Earth
FONTSIZE = 1.45 * 23 * 1.05 / EXTENT  # surface characters: large and bold
WEIGHT = "bold"
MARK_FONTSIZE = 23 * 1.05 / EXTENT  # epicenters and satellites
LINE_WIDTH = (
    1.4 * 150 / DPI
)  # rings, orbits, meshes, axes, field lines (points)
BACK_ALPHA = 0.35  # opacity of the lines passing behind the Earth
N_POINTS = 900  # surface points over the whole sphere
LAT0 = -4  # latitude facing the viewer: seen from just below the equator
LON_START = 150  # longitude facing the viewer at t = 0 (Pacific)
VIEW_ROLL = (
    6  # the picture is turned so that the North Pole leans left (degrees)
)
DURATION = 30  # seconds, one full turn of the Earth: the videos loop
FPS = 24

LAND_CHARS, OCEAN_CHARS = "#", "≈"

# Glyph styles: (color, alpha). Ocean and land have four shades, from day to
# night; then the accent color, for the marks drawn around the Earth
STYLES = [
    (OCEAN_COLOR, 0.95),
    (OCEAN_COLOR, 0.80),
    (OCEAN_COLOR, 0.60),
    (OCEAN_COLOR, 0.35),
    (LAND_COLOR, 1.00),
    (LAND_COLOR, 0.90),
    (LAND_COLOR, 0.70),
    (LAND_COLOR, 0.40),
    (ACCENT, 1.00),
    (ACCENT, 0.60),
    (ACCENT, 0.55),
]
OCEAN, LAND, MARK, MARK_FADING, MARK_PAST = 0, 4, 8, 9, 10

# Direction of the (fake) Sun in the viewer's frame (x right, y up, z towards
# the viewer): from the front left, so the night side is on the right
SUN = np.array([-0.75, 0.25, 0.6]) / np.linalg.norm([-0.75, 0.25, 0.6])


def shade(x, y, mu):
    """Shade index (0 lit, 3 night) of visible points (x, y, mu) of the sphere."""
    light = SUN[0] * x + SUN[1] * y + SUN[2] * mu
    return np.where(
        light > 0.55,
        0,
        np.where(light > 0.2, 1, np.where(light > -0.05, 2, 3)),
    )


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def fibonacci_sphere(n):
    """n points spread uniformly on the sphere, as (lat, lon) in degrees."""
    k = np.arange(n) + 0.5
    lat = np.degrees(np.arcsin(1 - 2 * k / n))
    lon = (np.degrees(np.pi * (1 + 5**0.5) * k) + 180) % 360 - 180
    return lat, lon


def orthographic_xy(lat, lon, lon0, lat0=LAT0, roll=VIEW_ROLL):
    """Orthographic projection on the unit disk: x, y and mu (cosine of the
    angle to the viewer, > 0 on the visible side). The picture is then turned
    by `roll` degrees."""
    phi, lam = np.radians(lat), np.radians(lon)
    phi0, lam0 = np.radians(lat0), np.radians(lon0)
    mu = np.sin(phi0) * np.sin(phi) + np.cos(phi0) * np.cos(phi) * np.cos(
        lam - lam0
    )
    x = np.cos(phi) * np.sin(lam - lam0)
    y = np.cos(phi0) * np.sin(phi) - np.sin(phi0) * np.cos(phi) * np.cos(
        lam - lam0
    )
    c, s = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    return c * x - s * y, s * x + c * y, mu


def project_xyz(xyz, lon0, lat0=LAT0):
    """Orthographic projection of 3D points (Earth frame, in Earth radii):
    x, y and depth (> 0 towards the viewer)."""
    r = np.linalg.norm(xyz, axis=-1)
    lat = np.degrees(np.arcsin(xyz[..., 2] / r))
    lon = np.degrees(np.arctan2(xyz[..., 1], xyz[..., 0]))
    x, y, mu = orthographic_xy(lat, lon, lon0, lat0)
    return r * x, r * y, r * mu


def project_line(xyz, lon0, hide=True):
    """Polyline for DepthLines: x, y and mu (depth over distance to the
    centre). With `hide`, x is NaN where the Earth hides the line."""
    x, y, depth = project_xyz(xyz, lon0)
    if hide:
        x = np.where((depth < 0) & (np.hypot(x, y) < 1.0), np.nan, x)
    return x, y, depth / np.linalg.norm(xyz, axis=-1)


def depth_alpha(mu, back=BACK_ALPHA, width=0.7):
    """Opacity of a line from its depth (mu, the cosine of the angle to the
    viewer): full in front, `back` behind, and a smooth change in between
    (over -width < mu < width) instead of a jump at the edge of the sphere."""
    t = np.clip((np.asarray(mu) + width) / (2 * width), 0, 1)
    return back + (1 - back) * t * t * (3 - 2 * t)


def fade(segments, depth, alpha, factor):
    """Multiply the opacity of the segments by `factor`, dropping those at 0."""
    keep = factor > 0
    return segments[keep], depth[keep], (alpha * factor)[keep]


class DepthLines:
    """Lines around the Earth whose opacity follows their depth.

    Each polyline is given as x, y and mu (depth normalised by the distance to
    the centre); NaN points break the line (e.g. where the Earth hides it).
    Segments in front of the sphere's centre plane are drawn over the globe,
    the others under it. `dash` cuts the lines into dashes of that length.
    With `limb` (a width in Earth radii), what passes behind the Earth fades
    out towards its edge instead of being cut there. With `outer` (radius,
    width), lines fade out as they approach that radius on screen, e.g. the
    edge of the picture.
    """

    def __init__(
        self,
        ax,
        color=ACCENT,
        linewidth=LINE_WIDTH,
        back=BACK_ALPHA,
        dash=None,
        limb=None,
        outer=None,
        zorders=(1, 3),
    ):
        self.rgb = matplotlib.colors.to_rgb(color)
        self.back, self.dash, self.limb, self.outer = back, dash, limb, outer
        self.layers = []
        for zorder in zorders:
            collection = LineCollection(
                [], linewidths=linewidth, capstyle="round", zorder=zorder
            )
            ax.add_collection(collection, autolim=False)
            self.layers.append(collection)

    def draw(self, polylines, offset=0.0):
        """Draw polylines (x, y, mu); `offset` shifts the dashes along them."""
        segments, depth = [np.empty((0, 2, 2))], [np.empty(0)]
        for x, y, mu in polylines:
            x, y, mu = map(np.asarray, (x, y, mu))
            ok = np.isfinite(x[:-1]) & np.isfinite(x[1:])
            if self.dash:
                length = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
                middle = np.nan_to_num((length[:-1] + length[1:]) / 2)
                ok &= ((middle - offset) // self.dash) % 2 == 0
            index = np.flatnonzero(ok)
            segments.append(
                np.stack(
                    [
                        np.column_stack([x[index], y[index]]),
                        np.column_stack([x[index + 1], y[index + 1]]),
                    ],
                    axis=1,
                )
            )
            depth.append((mu[index] + mu[index + 1]) / 2)
        segments, depth = np.concatenate(segments), np.concatenate(depth)
        alpha = depth_alpha(depth, self.back)
        rho = np.hypot(*segments.mean(axis=1).T)
        if self.limb:
            # Behind the Earth: fade out towards its edge, hidden over its disk
            factor = np.where(
                depth < 0, np.clip((rho - 1) / self.limb, 0, 1), 1.0
            )
            segments, depth, alpha = fade(segments, depth, alpha, factor)
            rho = np.hypot(*segments.mean(axis=1).T)
        if self.outer:
            radius, width = self.outer
            segments, depth, alpha = fade(
                segments, depth, alpha, np.clip((radius - rho) / width, 0, 1)
            )
        colors = np.column_stack([np.tile(self.rgb, (len(depth), 1)), alpha])
        for layer, keep in zip(self.layers, (depth < 0, depth >= 0)):
            layer.set_segments(segments[keep])
            layer.set_colors(colors[keep])


# ---------------------------------------------------------------------------
# Glyphs
# ---------------------------------------------------------------------------


def glyph_path(char, fontsize, weight="normal"):
    """Outline of a character, in points, centered on its cell."""
    path = TextPath(
        (0, 0),
        char,
        size=fontsize,
        prop=FontProperties(family=FONT, weight=weight),
    )
    return path.transformed(
        Affine2D().translate(-ADVANCE * fontsize / 2, -0.36 * fontsize)
    )


class GlyphLayer:
    """Characters drawn at arbitrary positions (data coordinates) on an axes,
    in one of the STYLES (color, alpha), `fontsize` points high."""

    def __init__(self, ax, fontsize, zorder=2, weight="normal", styles=STYLES):
        self.ax, self.styles, self.fontsize, self.zorder = (
            ax,
            styles,
            fontsize,
            zorder,
        )
        self.weight = weight
        self.collections = {}
        self.scale = Affine2D().scale(ax.figure.dpi / 72)

    def _collection(self, char, style):
        key = (char, style)
        if key not in self.collections:
            color, alpha = self.styles[style]
            collection = PathCollection(
                [glyph_path(char, self.fontsize, self.weight)],
                offsets=np.empty((0, 2)),
                offset_transform=self.ax.transData,
                facecolors=color,
                edgecolors="none",
                alpha=alpha,
                zorder=self.zorder,
            )
            collection.set_transform(self.scale)
            self.ax.add_collection(collection, autolim=False)
            self.collections[key] = collection
        return self.collections[key]

    def draw(self, x, y, chars, styles):
        """Show glyph chars[i] with style styles[i] at (x[i], y[i])."""
        xy = np.column_stack([np.ravel(x), np.ravel(y)])
        chars, styles = np.ravel(chars).astype(str), np.ravel(styles).astype(
            int
        )
        codes = (
            np.array([ord(c) for c in chars], dtype=np.int64) * 1000 + styles
        )
        order = np.argsort(codes, kind="stable")
        codes, xy = codes[order], xy[order]
        bounds = np.flatnonzero(np.diff(codes)) + 1
        used = set()
        for start, stop in zip(np.r_[0, bounds], np.r_[bounds, len(codes)]):
            if start == stop:
                continue
            key = (chr(codes[start] // 1000), int(codes[start] % 1000))
            self._collection(*key).set_offsets(xy[start:stop])
            used.add(key)
        for key, collection in self.collections.items():
            if key not in used:
                collection.set_offsets(np.empty((0, 2)))


# ---------------------------------------------------------------------------
# The turning Earth, base of every video
# ---------------------------------------------------------------------------


class HeroGlobe:
    """Transparent square figure with the Earth, made of characters, turning
    once during the video. Subclasses draw around it: they extend frame(t),
    which draws the Earth and returns the longitude facing the viewer."""

    name = "globe"  # output file name, without extension
    preview = 0.0  # fraction of the video shown by --preview

    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.lat, self.lon = fibonacci_sphere(N_POINTS)
        self.land = globe.is_land(self.lat, self.lon)
        self.chars = np.where(
            self.land,
            rng.choice(list(LAND_CHARS), N_POINTS),
            rng.choice(list(OCEAN_CHARS), N_POINTS),
        )

        self.fig = plt.figure(figsize=(SIZE, SIZE), dpi=DPI)
        self.fig.patch.set_alpha(0)  # transparent: the website sets the color
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set_xlim(-EXTENT, EXTENT)
        self.ax.set_ylim(-EXTENT, EXTENT)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.surface = GlyphLayer(self.ax, FONTSIZE, zorder=2, weight=WEIGHT)

    def frame(self, t):
        lon0 = (LON_START - 360 * t / DURATION + 180) % 360 - 180
        x, y, mu = orthographic_xy(self.lat, self.lon, lon0)
        front = mu > 0
        style = np.where(self.land, LAND, OCEAN) + shade(x, y, mu)
        self.surface.draw(x[front], y[front], self.chars[front], style[front])
        return lon0

    @classmethod
    def main(cls, parser=None, **kwargs):
        """Command line: render the video, or one frame with --preview. Extra
        options can be given with `parser`; its arguments go to the class."""
        parser = parser or argparse.ArgumentParser()
        parser.description = (cls.__doc__ or "").splitlines()[0]
        parser.add_argument(
            "--preview", action="store_true", help="render one frame as PNG"
        )
        args = vars(parser.parse_args())
        preview = args.pop("preview")
        OUTPUT.mkdir(exist_ok=True)
        figure = cls(**args, **kwargs)
        if preview:
            figure.frame(DURATION * cls.preview)
            figure.fig.savefig(OUTPUT / f"{cls.name}.png", transparent=True)
            print(f"saved {OUTPUT / cls.name}.png")
        else:
            render_transparent_video(
                figure.fig, figure.frame, OUTPUT / cls.name
            )


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------


def render_transparent_video(
    fig,
    draw_frame,
    stem,
    duration=DURATION,
    fps=FPS,
    matte=OCEAN_COLOR,
    vp9_crf=52,
    hevc_quality=35,
):
    """Render draw_frame(t) into two videos with an alpha channel, for the web.

    The figure background must be transparent. Fully transparent pixels get
    the color `matte` (by default matplotlib leaves them white): codecs bleed
    some color out of transparent areas, so it should match the edge of the
    picture. Writes, in one pass:
    - <stem>.webm: VP9 with alpha (Chrome, Firefox, Edge),
    - <stem>.mov: HEVC with premultiplied alpha (Safari),
    - <stem>.png: the first frame, as a transparent poster.
    """
    stem = Path(stem)
    matte_rgb = np.round(
        255 * np.array(matplotlib.colors.to_rgb(matte))
    ).astype(np.uint8)
    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    even = "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=0x00000000"
    command = [
        FFMPEG,
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgba",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        # VP9 with alpha
        "-vf",
        even,
        "-c:v",
        "libvpx-vp9",
        "-pix_fmt",
        "yuva420p",
        "-b:v",
        "0",
        "-crf",
        str(vp9_crf),
        "-auto-alt-ref",
        "0",
        "-row-mt",
        "1",
        "-deadline",
        "good",
        "-cpu-used",
        "2",
        str(stem.with_suffix(".webm")),
        # HEVC with alpha, hardware encoder of macOS (constant quality: it
        # smears badly at a low fixed bitrate). Safari reads its colors as
        # premultiplied by alpha, so premultiply them
        "-vf",
        even + ",premultiply=inplace=1",
        "-c:v",
        "hevc_videotoolbox",
        "-pix_fmt",
        "bgra",
        "-alpha_quality",
        "0.4",
        "-q:v",
        str(hevc_quality),
        "-tag:v",
        "hvc1",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-movflags",
        "+faststart",
        str(stem.with_suffix(".mov")),
    ]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as ffmpeg:
        for k in range(int(duration * fps)):
            draw_frame(k / fps)
            fig.canvas.draw()
            if k == 0:
                fig.savefig(stem.with_suffix(".png"), transparent=True)
            frame = np.array(fig.canvas.buffer_rgba())
            frame[frame[..., 3] == 0, :3] = matte_rgb
            ffmpeg.stdin.write(frame.tobytes())
            if k % fps == 0:
                print(f"\r{k // fps:3d}/{duration} s", end="", flush=True)
        ffmpeg.stdin.close()
    if ffmpeg.returncode:
        raise RuntimeError(f"ffmpeg failed with code {ffmpeg.returncode}")
    print(f"\rsaved {stem}.webm, {stem}.mov and {stem}.png")
