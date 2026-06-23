"""Validation helpers for finite-length truss results."""

from pathlib import Path

import numpy as np


def validate_frequencies(
    computed: Path, reference: Path, rtol: float = 1e-4, verbose: bool = True
) -> bool:
    """Compare modal frequency files."""
    comp = np.loadtxt(computed, delimiter=",", skiprows=1)
    ref = np.loadtxt(reference, delimiter=",", skiprows=1)
    n = min(len(comp), len(ref))
    freqs_comp = comp[:n, 1]
    freqs_ref = ref[:n, 1]
    errors = np.abs(freqs_comp - freqs_ref) / np.abs(freqs_ref)
    max_err = np.max(errors)

    if verbose:
        print(f"  Modes compared: {n}, max relative error: {max_err:.2e}")
        if max_err > rtol:
            worst = np.argmax(errors)
            print(
                f"  Worst mode: {int(comp[worst, 0])}, "
                f"comp={freqs_comp[worst]:.4f}, ref={freqs_ref[worst]:.4f}"
            )
    return bool(max_err < rtol)


def validate_tip_disp(
    computed: Path, reference: Path, rtol: float = 1e-3, verbose: bool = True
) -> bool:
    """Compare cantilever tip displacement files."""
    comp = np.loadtxt(computed, delimiter=",", skiprows=1, dtype=str)[
        :, 1:
    ].astype(float)
    ref = np.loadtxt(reference, delimiter=",", skiprows=1, dtype=str)[
        :, 1:
    ].astype(float)
    ok = np.allclose(comp, ref, rtol=rtol)
    if verbose:
        print(f"  Tip displacement match: {ok}")
        if not ok:
            max_diff = np.max(np.abs(comp - ref))
            max_ref = np.max(np.abs(ref))
            print(
                f"  Max absolute diff: {max_diff:.2e}, max ref value: {max_ref:.2e}"
            )
    return bool(ok)

