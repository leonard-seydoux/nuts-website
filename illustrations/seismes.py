"""Earthquake catalogues and how earthquakes are animated.

Catalogues are dicts of arrays: time (video seconds), lat, lon, magnitude,
depth, plus the real date of each event.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

DATA = Path(__file__).parent / "data"
USGS = (
    DATA / "usgs_2025_M5.5.csv"
)  # https://earthquake.usgs.gov/fdsnws/event/1/


def fake_catalogue(rng, duration, rate=10, start=datetime(2026, 1, 1)):
    """Random earthquakes: uniform on the sphere, Gutenberg-Richter magnitudes."""
    n = rng.poisson(duration * rate)
    time = np.sort(rng.uniform(0, duration, n))
    return {
        "time": time,
        "date": [start + timedelta(days=365 * t / duration) for t in time],
        "lat": np.degrees(np.arcsin(rng.uniform(-1, 1, n))),
        "lon": rng.uniform(-180, 180, n),
        "magnitude": np.minimum(4.5 + rng.exponential(1 / np.log(10), n), 9.0),
        "depth": np.minimum(rng.exponential(60, n), 700),
    }


def usgs_catalogue(duration, path=USGS):
    """The USGS ComCat catalogue, its year mapped onto the video duration."""
    with open(path) as file:
        rows = list(csv.DictReader(file))
    date = [
        datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
        for row in rows
    ]
    start = datetime(date[0].year, 1, 1, tzinfo=date[0].tzinfo)
    year = (
        datetime(start.year + 1, 1, 1, tzinfo=start.tzinfo) - start
    ).total_seconds()
    return {
        "time": np.array(
            [(d - start).total_seconds() / year * duration for d in date]
        ),
        "date": date,
        "lat": np.array([float(row["latitude"]) for row in rows]),
        "lon": np.array([float(row["longitude"]) for row in rows]),
        "magnitude": np.array([float(row["mag"]) for row in rows]),
        "depth": np.array([float(row["depth"]) for row in rows]),
    }


def save_catalogue(catalogue, path):
    with open(path, "w") as file:
        file.write("date,latitude,longitude,depth_km,magnitude\n")
        for date, lat, lon, depth, mag in zip(
            *(
                catalogue[key]
                for key in ("date", "lat", "lon", "depth", "magnitude")
            )
        ):
            file.write(
                f"{date:%Y-%m-%dT%H:%M:%S},{lat:.3f},{lon:.3f},{depth:.1f},{mag:.1f}\n"
            )


def select(catalogue, keep):
    """Subset of a catalogue."""
    return {key: np.asarray(value)[keep] if key != "date" else
            [d for d, k in zip(value, keep) if k] for key, value in catalogue.items()}


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


def lifetime(magnitude):
    """How long an earthquake stays animated, in seconds."""
    return 0.6 + 0.5 * (magnitude - 4.5)


def ring_radius(magnitude):
    """Final ring radius, in degrees."""
    return 2.5 * (magnitude - 4.0) ** 1.5


def small_circle(lat, lon, radius, n):
    """Points at an angular distance `radius` (degrees) around (lat, lon)."""
    phi, lam, delta = np.radians(lat), np.radians(lon), np.radians(radius)
    azimuth = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring_phi = np.arcsin(
        np.sin(phi) * np.cos(delta)
        + np.cos(phi) * np.sin(delta) * np.cos(azimuth)
    )
    ring_lam = lam + np.arctan2(
        np.sin(azimuth) * np.sin(delta) * np.cos(phi),
        np.cos(delta) - np.sin(phi) * np.sin(ring_phi),
    )
    return np.degrees(ring_phi), (np.degrees(ring_lam) + 180) % 360 - 180
