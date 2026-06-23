"""Template engine placeholder for periodic lattice unit analysis."""

from .case import PeriodicCase


class PeriodicTemplateEngine:
    """Phase-1 engine shell; template migration is handled in a later phase."""

    def build(self, case: PeriodicCase) -> str:
        return (
            f"! Periodic case placeholder: {case.name}\n"
            f"! NUM_SUB_SECTIONS = {case.num_subsections}\n"
            f"! LS = {case.ls}\n"
            f"! WS = {case.ws}\n"
        )

