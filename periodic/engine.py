"""Template engine for periodic lattice unit APDL inputs."""

from pathlib import Path

from .case import PeriodicCase


TEMPLATE_FILES = [
    "01_basic_model.inp",
    "02_pbc_stiffness.inp",
    "01_basic_model.inp",
    "03_rp_stiffness.inp",
    "01_basic_model.inp",
    "04_inertia.inp",
]


class PeriodicTemplateEngine:
    """Loads, concatenates, and substitutes periodic APDL templates."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self._cache: dict[str, str] = {}

    def _load(self, filename: str) -> str:
        if filename not in self._cache:
            self._cache[filename] = (self.templates_dir / filename).read_text()
        return self._cache[filename]

    def concatenate(self) -> str:
        """Return a full APDL script for basic, PBC, RP, and inertia steps."""
        return "\n".join(self._load(filename) for filename in TEMPLATE_FILES)

    @staticmethod
    def substitute(content: str, case: PeriodicCase) -> str:
        reps = {
            "__CASE_NAME_VAL__": case.name,
            "__NUM_SECTIONS_VAL__": str(case.num_sections),
            "__NUM_SUB_SECTIONS_VAL__": str(case.num_subsections),
            "__LS_VAL__": repr(case.ls),
            "__WS_VAL__": repr(case.ws),
            "__E_VAL__": repr(case.elastic_modulus),
            "__NU_VAL__": repr(case.poisson_ratio),
            "__RHO_VAL__": repr(case.density),
            "__ALPHA_VAL__": repr(case.thermal_expansion),
            "__LEG_B_VAL__": repr(case.leg_b),
            "__LEG_H_VAL__": repr(case.leg_h),
            "__LEG_TW_VAL__": repr(case.leg_tw),
            "__LEG_TF_VAL__": repr(case.leg_tf),
            "__DIAPH_B_VAL__": repr(case.diaphragm_b),
            "__DIAPH_H_VAL__": repr(case.diaphragm_h),
            "__DIAPH_TW_VAL__": repr(case.diaphragm_tw),
            "__DIAPH_TF_VAL__": repr(case.diaphragm_tf),
            "__BRACE_AREA_VAL__": repr(case.brace_area),
        }
        result = content
        for placeholder, value in reps.items():
            result = result.replace(placeholder, value)
        return result

    def build(self, case: PeriodicCase) -> str:
        """Build a complete APDL input for one periodic case."""
        return self.substitute(self.concatenate(), case)

