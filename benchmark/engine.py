"""Template engine: load, concatenate, and substitute APDL templates."""

from pathlib import Path

from .case import (
    AnalysisType,
    BCType,
    BraceType,
    CaseDefinition,
    DiaphType,
)

DIAPH_TEMPLATE_FILES: dict[DiaphType, str] = {
    DiaphType.X: "02_a_model_diaph_x.inp",
    DiaphType.SLASH: "02_b_model_diaph_slash.inp",
}

BRACE_TEMPLATE_FILES: dict[BraceType, str] = {
    BraceType.X: "03_a_model_brace_x.inp",
    BraceType.W: "03_b_model_brace_w.inp",
    BraceType.N: "03_c_model_brace_n.inp",
}

BC_TEMPLATE_FILES: dict[BCType, str] = {
    BCType.FIX_FREE: "04_a_bc_fix_free.inp",
    BCType.SIMPLE: "04_b_bc_simple.inp",
    BCType.ELASTIC: "04_c_bc_elastic.inp",
}

ANALYSIS_TEMPLATE_FILES: dict[AnalysisType, str] = {
    AnalysisType.MODAL: "05_modal_analysis.inp",
    AnalysisType.STATIC_CANTILEVER: "05_static_cantilever.inp",
    AnalysisType.STATIC_SIMPLE: "05_static_simple.inp",
}

STATIC_TEMPLATE_FILES: dict[str, str] = {
    "model_basic": "01_model_basic.inp",
    "post_shape": "06_modal_post_shape.inp",
    "plot_shape": "06_modal_plot_shape.inp",
}


class TemplateEngine:
    """Loads, concatenates, and substitutes placeholders in APDL templates."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self._cache: dict[str, str] = {}

    def _load_file(self, fname: str) -> str:
        """Load a template file by filename, with caching."""
        if fname not in self._cache:
            self._cache[fname] = (self.templates_dir / fname).read_text(
                encoding="utf-8"
            )
        return self._cache[fname]

    def _load_static(self, key: str) -> str:
        """Load a non-parametric stage template by key."""
        return self._load_file(STATIC_TEMPLATE_FILES[key])

    def template_files_for_case(self, case: CaseDefinition) -> list[str]:
        """Return ordered list of template filenames for a case."""
        files = [STATIC_TEMPLATE_FILES["model_basic"]]
        files.append(DIAPH_TEMPLATE_FILES[case.diaph])
        files.append(BRACE_TEMPLATE_FILES[case.brace])
        if case.bc != BCType.NONE:
            files.append(BC_TEMPLATE_FILES[case.bc])
        files.append(ANALYSIS_TEMPLATE_FILES[case.analysis])
        return files

    def resolve_sequence(self, case: CaseDefinition) -> list[str]:
        """Return ordered list of template filenames for a case."""
        return self.template_files_for_case(case)

    def concatenate(self, case: CaseDefinition) -> str:
        """Concatenate templates for a case into one APDL input string."""
        parts = [
            self._load_file(fname)
            for fname in self.template_files_for_case(case)
        ]
        return "\n".join(parts)

    @staticmethod
    def substitute(content: str, case: CaseDefinition) -> str:
        """Replace all __XXX_VAL__ and __XXX_STR__ placeholders."""
        reps = {
            "__CASE_NAME_VAL__": case.name,
            "__CASE_NAME_STR__": case.name,
            "__JobName_STR__": case.name,
            "__NumSections_VAL__": str(case.num_sections),
            "__NumSubsections_VAL__": str(case.num_subsections),
            "__Ls_VAL__": str(case.ls),
            "__Ws_VAL__": str(case.ws),
            "__NUM_MODES_VAL__": str(case.num_modes),
            "__TARGET_MODE_VAL__": (
                str(case.target_mode) if case.target_mode is not None else "1"
            ),
            "__NUM_PLOT_MODES_VAL__": (
                str(case.num_plot_modes)
                if hasattr(case, "num_plot_modes")
                and case.num_plot_modes is not None
                else "10"
            ),
        }
        result = content
        for placeholder, value in reps.items():
            result = result.replace(placeholder, value)
        return result

    def build(self, case: CaseDefinition) -> str:
        """Full pipeline: concatenate + substitute."""
        content = self.concatenate(case)
        return self.substitute(content, case)

    def build_post_shape(self, case: CaseDefinition, target_mode: int) -> str:
        """Build the 06_modal_post_shape template as a standalone input."""
        case_copy = CaseDefinition(
            name=case.name,
            num_sections=case.num_sections,
            num_subsections=case.num_subsections,
            ls=case.ls,
            ws=case.ws,
            diaph=case.diaph,
            brace=case.brace,
            bc=case.bc,
            analysis=case.analysis,
            num_modes=case.num_modes,
            target_mode=target_mode,
        )
        content = self._load_static("post_shape")
        return self.substitute(content, case_copy)

    def build_plot_shape(
        self, case: CaseDefinition, num_plot_modes: int
    ) -> str:
        """Build the 06_modal_plot_shape template as a standalone input."""
        case_copy = CaseDefinition(
            name=case.name,
            num_sections=case.num_sections,
            num_subsections=case.num_subsections,
            ls=case.ls,
            ws=case.ws,
            diaph=case.diaph,
            brace=case.brace,
            bc=case.bc,
            analysis=case.analysis,
            num_modes=case.num_modes,
            num_plot_modes=num_plot_modes,
        )
        content = self._load_static("plot_shape")
        return self.substitute(content, case_copy)
