"""Result parsers for finite-length truss ANSYS CSV outputs."""

from pathlib import Path

import numpy as np


def parse_freq(path: Path) -> np.ndarray:
    """Parse modal frequency CSV."""
    return np.loadtxt(path, delimiter=",", skiprows=1)


def parse_cantilever(path: Path) -> np.ndarray:
    """Parse cantilever tip displacement CSV."""
    raw = np.loadtxt(path, delimiter=",", skiprows=1, dtype=str)
    values = raw[:, 1:].astype(np.float64)
    return values


def parse_simple(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parse simple-support static CSV."""
    raw = np.loadtxt(path, delimiter=",", skiprows=1, dtype=str)
    load_cases = raw[:, 0].astype(float).astype(int)
    nodes = raw[:, 1].astype(float).astype(int)
    values = raw[:, 2:].astype(np.float64)
    return load_cases, nodes, values


def parse_shape(path: Path) -> tuple[float, np.ndarray]:
    """Parse mode shape CSV."""
    with open(path) as f:
        header = f.readline().strip()
    freq = float(header.split("=")[1].strip().split()[0])
    data = np.loadtxt(path, delimiter=",", skiprows=3)
    return freq, data

