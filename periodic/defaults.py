"""Default periodic cases.

Phase 1 only establishes the runner structure. Real cases are added when the
periodic APDL templates are migrated and parameterized.
"""

from .case import PeriodicCase


DEFAULT_CASES: list[PeriodicCase] = []

