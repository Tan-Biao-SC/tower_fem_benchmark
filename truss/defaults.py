"""Default finite-length truss cases."""

from benchmark.case import (
    AnalysisType,
    BCType,
    BraceType,
    CaseDefinition,
    DiaphType,
)


WIDTH_CASES = [
    CaseDefinition(
        f"W{w:.1f}_cant_modal",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=w,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    )
    for w in [1.5, 2.0, 3.0, 4.0, 6.0]
]

SECTION_CASES = [
    CaseDefinition(
        f"S{ns}_cant_modal",
        num_sections=ns,
        num_subsections=4,
        ls=1.5,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    )
    for ns in [4, 6, 8, 10, 15, 20]
]

SUBSECTION_CASES = [
    CaseDefinition(
        f"NC{nc}_cant_modal",
        num_sections=10,
        num_subsections=nc,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    )
    for nc in [2, 3, 4, 6, 8]
]

BRACE_CASES = [
    CaseDefinition(
        f"brace_{bt.value}_cant_static",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=bt,
        bc=BCType.FIX_FREE,
        analysis=AnalysisType.STATIC_CANTILEVER,
    )
    for bt in [BraceType.X, BraceType.W, BraceType.N]
]

SIMPLE_CASES = [
    CaseDefinition(
        "xbrace_xdiaph_simple_static",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.SIMPLE,
        analysis=AnalysisType.STATIC_SIMPLE,
    ),
]

FREE_MODAL_CASES = [
    CaseDefinition(
        "xbrace_xdiaph_free_modal",
        num_sections=10,
        num_subsections=2,
        ls=3.0,
        ws=2.0,
        diaph=DiaphType.X,
        brace=BraceType.X,
        bc=BCType.NONE,
        analysis=AnalysisType.MODAL,
        num_modes=30,
    ),
]

ALL_CASES = (
    WIDTH_CASES
    + SECTION_CASES
    + SUBSECTION_CASES
    + BRACE_CASES
    + SIMPLE_CASES
    + FREE_MODAL_CASES
)

