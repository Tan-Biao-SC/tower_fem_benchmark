"""Case definition for finite-length truss analysis."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DiaphType(str, Enum):
    """Diaphragm type selecting the 02_* template."""

    X = "x"
    SLASH = "slash"


class BraceType(str, Enum):
    """Brace type selecting the 03_* template."""

    X = "x"
    W = "w"
    N = "n"


class BCType(str, Enum):
    """Boundary condition type selecting the 04_* template.

    NONE means free-free, with no BC template concatenated.
    """

    NONE = "none"
    FIX_FREE = "fix_free"
    SIMPLE = "simple"
    ELASTIC = "elastic"


class AnalysisType(str, Enum):
    """Analysis type selecting the 05_* template."""

    MODAL = "modal"
    STATIC_CANTILEVER = "static_cantilever"
    STATIC_SIMPLE = "static_simple"


@dataclass
class CaseDefinition:
    """All parameters needed to generate and run one truss case."""

    name: str
    num_sections: int
    num_subsections: int
    ls: float
    ws: float
    diaph: DiaphType = DiaphType.X
    brace: BraceType = BraceType.X
    bc: BCType = BCType.NONE
    analysis: AnalysisType = AnalysisType.MODAL
    num_modes: int = 30
    target_mode: Optional[int] = None
    num_plot_modes: Optional[int] = None

    @property
    def tower_height(self) -> float:
        """Total tower height in metres."""
        return self.num_sections * self.num_subsections * self.ls

    @property
    def num_node_planes(self) -> int:
        """Number of node planes along the tower height."""
        return self.num_sections * self.num_subsections + 1

