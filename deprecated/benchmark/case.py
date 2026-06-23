"""Case definition for parametric FEM benchmark."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DiaphType(str, Enum):
    """Diaphragm type — selects 02_a or 02_b template."""

    X = "x"
    SLASH = "slash"


class BraceType(str, Enum):
    """Brace type — selects 03_a, 03_b, or 03_c template."""

    X = "x"
    W = "w"
    N = "n"


class BCType(str, Enum):
    """Boundary condition type — selects 04_a, 04_b, or 04_c template.
    NONE means free-free (no BC template concatenated).
    """

    NONE = "none"
    FIX_FREE = "fix_free"
    SIMPLE = "simple"
    ELASTIC = "elastic"


class AnalysisType(str, Enum):
    """Analysis type — selects 05_modal, 05_static_cantilever, or 05_static_simple."""

    MODAL = "modal"
    STATIC_CANTILEVER = "static_cantilever"
    STATIC_SIMPLE = "static_simple"


@dataclass
class CaseDefinition:
    """All parameters needed to generate and run one ANSYS case."""

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
    target_mode: Optional[int] = None  # for 06_modal_post_shape only
    num_plot_modes: Optional[int] = None  # for 06_modal_plot_shape only

    @property
    def tower_height(self) -> float:
        """Total tower height in metres."""
        return self.num_sections * self.num_subsections * self.ls

    @property
    def num_node_planes(self) -> int:
        """Number of node planes along the tower height."""
        return self.num_sections * self.num_subsections + 1
