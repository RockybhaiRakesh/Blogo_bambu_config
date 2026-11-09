"""
Hardware and Material Compatibility Validator module.
Enforces thermal constraints, enclosure requirements, nozzle abrasion safety,
and moisture drying protocols between selected printer hardware and filament materials.
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional
from printmate.profiles.printer_profiles import PrinterProfile
from printmate.profiles.filament_profiles import FilamentProfile

@dataclass
class CompatibilityResult:
    """Audit outcome of printer hardware vs filament material pairing."""
    is_compatible: bool
    is_safe_to_slice: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    operational_notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "COMPATIBLE" if self.is_compatible else "INCOMPATIBLE"
        return (
            f"Compatibility Check [{status}]: "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.operational_notes)} notes"
        )

class SettingsValidator:
    """Validates cross-domain constraints across printers, filaments, and geometry."""

    @classmethod
    def validate_pairing(
        cls,
        printer: PrinterProfile,
        filament: FilamentProfile
    ) -> CompatibilityResult:
        """Audits hardware capabilities against material printing requirements."""
        errors: List[str] = []
        warnings: List[str] = []
        notes: List[str] = []

        # 1. Thermal Envelope Verification
        if filament.nozzle_temp_recommended > printer.max_nozzle_temp:
            errors.append(
                f"Thermal Limit Exceeded: {filament.brand} {filament.material_name} requires "
                f"{filament.nozzle_temp_recommended:.0f}°C, exceeding {printer.name}'s max nozzle temperature ({printer.max_nozzle_temp:.0f}°C)."
            )

        if filament.bed_temp_recommended > printer.max_bed_temp:
            errors.append(
                f"Bed Thermal Limit Exceeded: {filament.brand} {filament.material_name} requires "
                f"{filament.bed_temp_recommended:.0f}°C bed, exceeding {printer.name}'s max bed temperature ({printer.max_bed_temp:.0f}°C)."
            )

        # 2. Enclosure Requirement for Warp-Prone Engineering Plastics
        if filament.enclosure_required and not printer.has_enclosure:
            warnings.append(
                f"ENCLOSURE MISSING: {filament.material_name} experiences severe inter-layer cracking "
                f"and thermal contraction warping without an enclosed build chamber. "
                f"{printer.name} is an open-frame printer. Brim and draft shield strongly advised."
            )

        # 3. Abrasive Composite Wear
        if filament.is_abrasive and not printer.has_hardened_nozzle:
            warnings.append(
                f"NOZZLE WEAR HAZARD: {filament.material_name} contains chopped fiber reinforcements. "
                f"{printer.name} has standard non-hardened nozzles which will suffer rapid orifice enlargement. "
                f"Upgrade to Hardened Steel nozzle (0.4mm or 0.6mm) recommended."
            )

        # 4. Moisture Sensitivity Protocol
        if filament.moisture_sensitive:
            drying_info = (
                f"Dry at {filament.drying_temp_c:.0f}°C for {filament.drying_duration_hrs:.0f} hours."
                if filament.drying_temp_c and filament.drying_duration_hrs else "Dry thoroughly before printing."
            )
            notes.append(
                f"HYGROSCOPIC MATERIAL: {filament.material_name} absorbs ambient humidity. {drying_info}"
            )

        is_compatible = len(errors) == 0
        is_safe_to_slice = is_compatible

        return CompatibilityResult(
            is_compatible=is_compatible,
            is_safe_to_slice=is_safe_to_slice,
            errors=errors,
            warnings=warnings,
            operational_notes=notes
        )

    @classmethod
    def validate_settings(
        cls,
        settings: Any,
        printer_id: Optional[str] = None,
        filament_id: Optional[str] = None
    ) -> CompatibilityResult:
        """Convenience auditor for an OptimizedSettings object or raw identifiers."""
        if hasattr(settings, "printer") and hasattr(settings, "filament"):
            return cls.validate_pairing(settings.printer, settings.filament)
        from printmate.profiles.printer_profiles import PrinterProfileRegistry
        from printmate.profiles.filament_profiles import FilamentProfileRegistry
        p = PrinterProfileRegistry.get_profile(printer_id or "Bambu Lab A1")
        f = FilamentProfileRegistry.get_profile(filament_id or "pla_basic")
        return cls.validate_pairing(p, f)
