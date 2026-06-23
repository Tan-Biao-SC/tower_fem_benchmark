"""Result parser: read ANSYS output CSV files into numpy arrays."""

import numpy as np
from pathlib import Path


def parse_freq(path: Path) -> np.ndarray:
    """Parse modal frequency CSV.

    Returns array shape (n_modes, 2): [[mode_num, freq_hz], ...].
    """
    return np.loadtxt(path, delimiter=",", skiprows=1)


def parse_cantilever(path: Path) -> np.ndarray:
    """Parse cantilever tip displacement CSV.

    Returns array shape (6, 7): rows = load cases (FX..MZ),
    cols = (label, ux, uy, uz, rx, ry, rz) — label column is string.
    The numeric data is shape (6, 6).
    """
    raw = np.loadtxt(path, delimiter=",", skiprows=1, dtype=str)
    values = raw[:, 1:].astype(np.float64)
    return values


def parse_simple(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parse simple-support static CSV.

    Returns (load_cases, nodes, values) where:
      - load_cases: (N,) int array of load case numbers
      - nodes:      (N,) int array of node indices
      - values:     (N, 6) float array of (ux, uy, uz, rx, ry, rz)
    """
    raw = np.loadtxt(path, delimiter=",", skiprows=1, dtype=str)
    load_cases = raw[:, 0].astype(float).astype(int)
    nodes = raw[:, 1].astype(float).astype(int)
    values = raw[:, 2:].astype(np.float64)
    return load_cases, nodes, values


def parse_shape(path: Path) -> tuple[float, np.ndarray]:
    """Parse mode shape CSV.

    Returns (freq_hz, station_data) where station_data is (n_stations, 8):
    [station_idx, x, ux, uy, uz, rx, ry, rz].
    """
    with open(path) as f:
        header = f.readline().strip()
    freq = float(header.split("=")[1].strip().split()[0])
    data = np.loadtxt(path, delimiter=",", skiprows=3)
    return freq, data
