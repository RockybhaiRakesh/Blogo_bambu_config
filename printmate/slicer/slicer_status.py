"""
Slicer and Project Validation Status Codes for PRINTMATE AI.
Defines explicit engineering states across 3MF project packaging, slicer integration,
G-code validation, and physical production boundaries.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class SlicerStatus(str, Enum):
    """
    Standardized validation and execution states.
    Guarantees unambiguous progress tracking and prevents false claims of print success.
    """
    PROJECT_VALIDATION_FAILED = "PROJECT_VALIDATION_FAILED"
    SLICER_NOT_AVAILABLE = "SLICER_NOT_AVAILABLE"
    SLICING_REQUIRED = "SLICING_REQUIRED"
    SLICING_FAILED = "SLICING_FAILED"
    GCODE_VALIDATION_FAILED = "GCODE_VALIDATION_FAILED"
    SLICE_VALIDATED = "SLICE_VALIDATED"
    PHYSICAL_PRINT_NOT_VERIFIED = "PHYSICAL_PRINT_NOT_VERIFIED"

@dataclass
class SlicerExecutionRecord:
    """Audit record capturing the exact environment and status of a slicing event."""
    status: SlicerStatus
    slicer_name: str = "Bambu Studio"
    slicer_version: Optional[str] = None
    printer_profile: str = "Bambu Lab A1"
    filament_profile: str = "Bambu PLA Basic"
    process_profile: str = "0.20mm Standard @BBL A1"
    project_path: Optional[str] = None
    gcode_path: Optional[str] = None
    is_headless_cli: bool = False
    is_gui_assisted: bool = False
    is_gcode_validated: bool = False
    physical_print_confirmed: bool = False  # NEVER True from software slice alone
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        s = f"Slicer Status [{self.status.value}]: {self.slicer_name}"
        if self.slicer_version:
            s += f" (v{self.slicer_version})"
        s += f" | Printer: {self.printer_profile} | Filament: {self.filament_profile}"
        if self.errors:
            s += f"\n  Errors: {'; '.join(self.errors)}"
        if self.warnings:
            s += f"\n  Warnings: {'; '.join(self.warnings)}"
        return s

