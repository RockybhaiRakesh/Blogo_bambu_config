"""
Material and Printer-Aware Connector Tolerance Management module.
Maintains granular engineering tolerance configurations per machine, nozzle, filament type,
and desired mechanical fit class (slip-fit, press-fit, loose-fit).
Enforces strict distinction between theoretical (simulated) and physically calibrated tolerances.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

@dataclass
class ToleranceProfile:
    """Configurable tolerance envelope for mechanical 3D printed joints."""
    printer_model: str = "Bambu Lab A1"
    nozzle_diameter: float = 0.4
    material: str = "pla_basic"
    fit_class: str = "slip_fit"       # "slip_fit", "press_fit", "loose_fit"
    radial_clearance: float = 0.25   # Radial clearance delta in mm
    axial_relief: float = 1.00       # Vertical air gap at socket bottom in mm
    pin_height: float = 5.00         # Standard pin height in mm
    is_physically_calibrated: bool = False  # False = Simulated / Heuristic; True = Physically tested
    notes: str = "Standard theoretical tolerance baseline for 0.4mm nozzle."

    def summary(self) -> str:
        cal_str = "PHYSICALLY CALIBRATED" if self.is_physically_calibrated else "THEORETICAL (UNTESTED)"
        return (
            f"ToleranceProfile [{self.printer_model} | {self.material.upper()} | {self.fit_class}]: "
            f"Radial Dr = {self.radial_clearance:.2f}mm, Axial Dz = {self.axial_relief:.2f}mm [{cal_str}]"
        )

class ToleranceManager:
    """Manages machine- and material-specific connector tolerance registries."""

    _PROFILES: Dict[str, ToleranceProfile] = {
        # Bambu Lab A1 - 0.4mm Nozzle Profiles
        "bambu_a1_0.4_pla_basic_slip_fit": ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="pla_basic",
            fit_class="slip_fit",
            radial_clearance=0.22,
            axial_relief=0.80,
            notes="Standard slip-fit for clean PLA Basic."
        ),
        "bambu_a1_0.4_pla_basic_press_fit": ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="pla_basic",
            fit_class="press_fit",
            radial_clearance=0.15,
            axial_relief=0.60,
            notes="Tight friction press-fit; requires firm manual insertion."
        ),
        "bambu_a1_0.4_pla_basic_loose_fit": ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="pla_basic",
            fit_class="loose_fit",
            radial_clearance=0.30,
            axial_relief=1.00,
            notes="Loose clearance fit for glue/epoxy bonding."
        ),
        "bambu_a1_0.4_pla_matte_slip_fit": ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="pla_matte",
            fit_class="slip_fit",
            radial_clearance=0.25,
            axial_relief=1.00,
            notes="Compensates for matte surface microscopic texture and friction."
        ),
        "bambu_a1_0.4_pla_silk_slip_fit": ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="pla_silk",
            fit_class="slip_fit",
            radial_clearance=0.28,
            axial_relief=1.00,
            notes="Compensates for Silk PLA post-extrusion die swelling."
        ),
        "bambu_a1_0.4_petg_slip_fit": ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="petg",
            fit_class="slip_fit",
            radial_clearance=0.26,
            axial_relief=1.00,
            notes="Compensates for PETG oozing and dimensional expansion."
        ),
    }

    @classmethod
    def get_profile(
        cls,
        material: str = "pla_basic",
        printer: str = "Bambu Lab A1",
        nozzle: float = 0.4,
        fit_class: str = "slip_fit"
    ) -> ToleranceProfile:
        """
        Retrieves matching tolerance profile. Falls back to standard slip-fit baseline if not found.
        """
        mat_clean = material.lower().replace("-", "_")
        key = f"bambu_a1_{nozzle}_{mat_clean}_{fit_class}"

        if key in cls._PROFILES:
            return cls._PROFILES[key]

        # Generic fallback
        return ToleranceProfile(
            printer_model=printer,
            nozzle_diameter=nozzle,
            material=mat_clean,
            fit_class=fit_class,
            radial_clearance=0.25,
            axial_relief=1.00,
            is_physically_calibrated=False,
            notes="Generic uncalibrated fallback baseline."
        )

    @classmethod
    def register_calibrated_profile(
        cls,
        profile: ToleranceProfile
    ) -> None:
        """
        Registers a verified physically calibrated profile into the in-memory registry.
        """
        profile.is_physically_calibrated = True
        key = f"bambu_a1_{profile.nozzle_diameter}_{profile.material}_{profile.fit_class}"
        cls._PROFILES[key] = profile

    @classmethod
    def list_profiles(cls) -> List[ToleranceProfile]:
        """Returns all configured tolerance profiles."""
        return list(cls._PROFILES.values())
