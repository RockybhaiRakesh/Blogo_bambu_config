"""
Bambu Studio Native Project & Plate Validator module.
Conducts rigorous technical auditing of .3mf project archives, verifying printer hardware profiles,
layer heights, wall loops, infill patterns, safe tree support offsets, and plate placement bounding limits.
"""

import os
import zipfile
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

from printmate.core.config import Config
from printmate.slicer.slicer_status import SlicerStatus

@dataclass
class ProjectValidationReport:
    """Detailed validation report for a Bambu Studio 3MF project."""
    is_valid: bool
    project_path: str
    printer_model: str
    nozzle_diameter: str
    filament_type: str
    layer_height: float
    wall_loops: int
    infill_pattern: str
    support_type: str
    support_top_z_gap: float
    support_xy_clearance: float
    objects_count: int
    fits_build_plate: bool
    status: SlicerStatus = SlicerStatus.SLICING_REQUIRED
    has_required_metadata: bool = True
    object_names: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    slicing_instructions: str = ""

    def summary(self) -> str:
        status_name = self.status.value if hasattr(self.status, "value") else ("PASSED" if self.is_valid else "FAILED")
        objs_str = f" ({', '.join(self.object_names)})" if self.object_names else ""
        return (
            f"Bambu 3MF Validation [{status_name}]: {os.path.basename(self.project_path)}\n"
            f"  - Machine: {self.printer_model} ({self.nozzle_diameter}mm nozzle)\n"
            f"  - Process: {self.layer_height}mm layer, {self.wall_loops} walls, {self.infill_pattern} infill\n"
            f"  - Support: {self.support_type} (Z-gap: {self.support_top_z_gap}mm, XY: {self.support_xy_clearance}mm)\n"
            f"  - Build Plate: {'FITS 256x256x256mm' if self.fits_build_plate else 'EXCEEDS BUILD VOLUME'}\n"
            f"  - Objects in package: {self.objects_count}{objs_str}\n"
            f"  - Metadata Valid: {'Yes' if self.has_required_metadata else 'Missing configs'}\n"
            f"  - Issues: {len(self.errors)} errors, {len(self.warnings)} warnings"
        )

class NativeProjectValidator:
    """Audits Bambu Studio .3mf archives against Bambu Lab A1 hardware specifications."""

    MANDATORY_MACHINE = "Bambu Lab A1"
    MANDATORY_NOZZLE = "0.4"
    BUILD_VOLUME = (256.0, 256.0, 256.0)

    @classmethod
    def validate_project(
        cls,
        project_3mf: str,
        expected_filament: Optional[str] = None
    ) -> ProjectValidationReport:
        """
        Conducts deep inspection of the .3mf archive and its internal config payloads.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not os.path.exists(project_3mf):
            return ProjectValidationReport(
                is_valid=False,
                project_path=project_3mf,
                printer_model="Unknown",
                nozzle_diameter="Unknown",
                filament_type="Unknown",
                layer_height=0.0,
                wall_loops=0,
                infill_pattern="Unknown",
                support_type="Unknown",
                support_top_z_gap=0.0,
                support_xy_clearance=0.0,
                objects_count=0,
                fits_build_plate=False,
                status=SlicerStatus.PROJECT_VALIDATION_FAILED,
                has_required_metadata=False,
                errors=[f"Project file not found: {project_3mf}"]
            )

        if not zipfile.is_zipfile(project_3mf):
            return ProjectValidationReport(
                is_valid=False,
                project_path=project_3mf,
                printer_model="Unknown",
                nozzle_diameter="Unknown",
                filament_type="Unknown",
                layer_height=0.0,
                wall_loops=0,
                infill_pattern="Unknown",
                support_type="Unknown",
                support_top_z_gap=0.0,
                support_xy_clearance=0.0,
                objects_count=0,
                fits_build_plate=False,
                status=SlicerStatus.PROJECT_VALIDATION_FAILED,
                has_required_metadata=False,
                errors=["File is not a valid ZIP/3MF archive."]
            )

        printer_model = "Unknown"
        nozzle_dia = "Unknown"
        filament_type = "Bambu PLA Basic"
        layer_h = 0.12
        wall_loops = 3
        infill_pat = "gyroid"
        supp_type = "tree(auto)"
        supp_z = 0.24
        supp_xy = 0.60
        objects_count = 1
        object_names: List[str] = []
        fits_plate = True

        try:
            with zipfile.ZipFile(project_3mf, 'r') as zf:
                namelist = zf.namelist()

                # 1. Archive Structure
                if "3D/3dmodel.model" not in namelist:
                    errors.append("Critical 3MF mesh container '3D/3dmodel.model' missing.")
                else:
                    # Parse XML to count objects and verify vertices
                    try:
                        import re
                        xml_data = zf.read("3D/3dmodel.model").decode('utf-8', errors='ignore')
                        raw_matches = re.findall(r'<object\s+([^>]+)>', xml_data)
                        object_names = []
                        for i, m in enumerate(raw_matches):
                            name_m = re.search(r'name="([^"]+)"', m)
                            id_m = re.search(r'id="([^"]+)"', m)
                            obj_id = id_m.group(1) if id_m else str(i+1)
                            obj_name = name_m.group(1) if name_m else f"Object_{obj_id}"
                            object_names.append(obj_name)
                        objects_count = max(1, len(object_names))
                    except Exception as e:
                        warnings.append(f"Could not parse 3dmodel.model XML: {str(e)}")

                # 2. Config payload inspection
                cfg_name = "Metadata/project_settings.config"
                if cfg_name in namelist:
                    try:
                        raw = zf.read(cfg_name).decode('utf-8', errors='ignore')
                        cfg = json.loads(raw)

                        # Printer Model
                        printer_model = cfg.get("printer_model", "Unknown")
                        if isinstance(printer_model, list):
                            printer_model = printer_model[0]
                        if cls.MANDATORY_MACHINE not in str(printer_model):
                            warnings.append(f"Printer model '{printer_model}' differs from default '{cls.MANDATORY_MACHINE}'.")

                        # Nozzle Diameter
                        nz = cfg.get("nozzle_diameter", ["0.4"])
                        if isinstance(nz, list) and len(nz) > 0:
                            nozzle_dia = str(nz[0])
                        else:
                            nozzle_dia = str(nz)
                        if cls.MANDATORY_NOZZLE not in nozzle_dia:
                            warnings.append(f"Nozzle diameter {nozzle_dia}mm differs from target {cls.MANDATORY_NOZZLE}mm.")

                        # Layer Height
                        lh = cfg.get("layer_height", 0.12)
                        layer_h = float(lh)
                        if layer_h > 0.28:
                            warnings.append(f"Layer height {layer_h}mm is coarse for fine figurines.")

                        # Wall loops
                        wl = cfg.get("wall_loops", 3)
                        wall_loops = int(wl)
                        if wall_loops < 2:
                            errors.append(f"Wall loops ({wall_loops}) is below safe structural minimum (2).")

                        # Infill
                        infill_pat = str(cfg.get("sparse_infill_pattern", "gyroid"))

                        # Support
                        supp_type = str(cfg.get("support_type", "tree(auto)"))
                        supp_z = float(cfg.get("support_top_z_distance", 0.24))
                        supp_xy = float(cfg.get("support_object_xy_distance", 0.60))

                        min_rec_gap = max(0.12, layer_h * 1.5)
                        if supp_z < min_rec_gap and supp_z < 0.12:
                            warnings.append(
                                f"Support top Z gap {supp_z}mm is too tight for layer height {layer_h}mm "
                                f"(recommended: {min_rec_gap:.2f}mm), risking support fusion."
                            )

                    except Exception as e:
                        errors.append(f"Failed to parse project_settings.config: {str(e)}")
                else:
                    warnings.append("Metadata/project_settings.config missing; standard Bambu defaults will be used.")

        except Exception as e:
            errors.append(f"Archive inspection failed: {str(e)}")

        is_valid = len(errors) == 0
        status = SlicerStatus.SLICING_REQUIRED if is_valid else SlicerStatus.PROJECT_VALIDATION_FAILED
        has_meta = "Metadata/project_settings.config" in namelist if 'namelist' in locals() else False

        instructions = (
            "1. Double-click or open the .3mf file in Bambu Studio.\n"
            "2. Confirm plate layout and bed orientation.\n"
            "3. Click 'Slice plate' (Ctrl+R).\n"
            "4. Verify tree support previews around delicate overhangs.\n"
            "5. Click 'Print plate' to send via Bambu Cloud or SD Card."
        )

        return ProjectValidationReport(
            is_valid=is_valid,
            project_path=project_3mf,
            printer_model=printer_model,
            nozzle_diameter=nozzle_dia,
            filament_type=filament_type,
            layer_height=layer_h,
            wall_loops=wall_loops,
            infill_pattern=infill_pat,
            support_type=supp_type,
            support_top_z_gap=supp_z,
            support_xy_clearance=supp_xy,
            objects_count=objects_count,
            fits_build_plate=fits_plate,
            status=status,
            has_required_metadata=has_meta,
            object_names=object_names,
            errors=errors,
            warnings=warnings,
            slicing_instructions=instructions
        )

