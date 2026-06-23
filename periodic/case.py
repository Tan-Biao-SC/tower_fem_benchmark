"""Case definitions for periodic lattice unit analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PeriodicCase:
    """Minimal periodic case shell for the phase-1 runner."""

    name: str
    num_subsections: int
    ls: float
    ws: float

