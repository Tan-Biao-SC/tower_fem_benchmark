"""ANSYS process helpers shared by analysis modules."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


DEFAULT_ANSYS_EXE = "ansys190.exe"


def run_ansys(
    input_path: Path,
    log_path: Path,
    work_dir: Path,
    ansys_exe: str = DEFAULT_ANSYS_EXE,
) -> subprocess.CompletedProcess:
    """Run ANSYS APDL in batch mode without shell string expansion."""
    input_path = Path(input_path)
    log_path = Path(log_path)
    work_dir = Path(work_dir)

    work_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [ansys_exe, "-b", "-i", str(input_path), "-o", str(log_path)]
    return subprocess.run(cmd, cwd=str(work_dir))


def collect_files(
    source_dir: Path,
    target_dir: Path,
    patterns: list[str],
) -> list[Path]:
    """Move matching files from an ANSYS work directory to a result directory."""
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    collected: list[Path] = []
    for pattern in patterns:
        for source_path in source_dir.glob(pattern):
            target_path = target_dir / source_path.name
            shutil.move(str(source_path), str(target_path))
            collected.append(target_path)
    return collected

