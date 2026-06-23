"""Default periodic lattice unit cases."""

from .case import PeriodicCase


REFERENCE_CASE = PeriodicCase(
    name="n2_default",
    num_subsections=2,
    ls=2.023 / 2.0,
    ws=2.0,
)

SUBSECTION_CASES = [
    PeriodicCase(
        name=f"n{n}_default",
        num_subsections=n,
        ls=2.023 / n,
        ws=2.0,
    )
    for n in [1, 4]
]

DEFAULT_CASES: list[PeriodicCase] = [REFERENCE_CASE, *SUBSECTION_CASES]

