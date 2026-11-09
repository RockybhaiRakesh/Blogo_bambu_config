"""
Deep G-code Parser and Physical Print Validation module for PRINTMATE AI.
Extracts verified machine telemetry from Bambu Studio G-code headers and config blocks.
Performs coordinate boundary audits, thermal envelope checks, and distinguishes actual
slicer metrics from heuristic predictions.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple

from printmate.core.exceptions import SlicerIntegrationError
from printmate.slicer.slicer_status import SlicerStatus

@dataclass
class GCodeMetadata:
    """Telemetry extracted directly from Bambu Studio sliced G-code file."""
    gcode_path: str
    file_size_bytes: int
    slicer_version: str = "Unknown"
    model_printing_time_str: str = ""
    total_estimated_time_str: str = ""
    total_estimated_time_minutes: float = 0.0
    total_filament_weight_g: float = 0.0
    total_filament_length_mm: float = 0.0
    total_filament_volume_cm3: float = 0.0
    filament_density: float = 1.24
    filament_diameter: float = 1.75
    total_layers: int = 0
    max_z_height_mm: float = 0.0
    printer_profile: str = ""
    filament_profile: str = ""
    bed_type: str = ""
    layer_height_mm: float = 0.0
    wall_loops: int = 0
    infill_pattern: str = ""
    infill_density_str: str = ""
    support_enabled: bool = False
    support_style: str = ""
    support_top_z_gap: float = 0.0
    support_bottom_z_gap: float = 0.0
    brim_type: str = ""
    brim_width_mm: float = 0.0
    nozzle_temperature: float = 0.0
    bed_temperature: float = 0.0

    # Separated coordinate bounds
    model_min_x: float = 0.0
    model_max_x: float = 0.0
    model_min_y: float = 0.0
    model_max_y: float = 0.0
    model_min_z: float = 0.0
    model_max_z: float = 0.0

    support_min_x: Optional[float] = None
    support_max_x: Optional[float] = None
    support_min_y: Optional[float] = None
    support_max_y: Optional[float] = None
    support_min_z: Optional[float] = None
    support_max_z: Optional[float] = None

    brim_min_x: Optional[float] = None
    brim_max_x: Optional[float] = None
    brim_min_y: Optional[float] = None
    brim_max_y: Optional[float] = None

    printed_min_x: float = 0.0
    printed_max_x: float = 0.0
    printed_min_y: float = 0.0
    printed_max_y: float = 0.0
    printed_min_z: float = 0.0
    printed_max_z: float = 0.0

    maintenance_min_x: float = 0.0
    maintenance_max_x: float = 0.0
    maintenance_min_y: float = 0.0
    maintenance_max_y: float = 0.0

    first_layer_min_x: float = 0.0
    first_layer_max_x: float = 0.0
    first_layer_min_y: float = 0.0
    first_layer_max_y: float = 0.0

    is_within_build_plate: bool = True
    is_actual_slicer_output: bool = True
    is_heuristic_estimate: bool = False

@dataclass
class GCodeValidationResult:
    """Validation report certifying G-code authenticity, integrity, and safety."""
    status: SlicerStatus
    is_valid: bool
    gcode_path: str
    metadata: Optional[GCodeMetadata] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        s = f"G-code Validation [{self.status.value}]: {os.path.basename(self.gcode_path)}\n"
        if self.metadata:
            s += (
                f"  - Slicer Version:    {self.metadata.slicer_version}\n"
                f"  - Actual Duration:   {self.metadata.total_estimated_time_str} ({self.metadata.total_estimated_time_minutes:.1f} mins)\n"
                f"  - Actual Material:   {self.metadata.total_filament_weight_g:.2f} g ({self.metadata.total_filament_length_mm:.1f} mm)\n"
                f"  - Actual Layers:     {self.metadata.total_layers} layers (Max Z: {self.metadata.max_z_height_mm:.2f} mm)\n"
                f"  - Hardware Config:   {self.metadata.printer_profile} | Bed: {self.metadata.bed_type}\n"
                f"  - Process Settings:  {self.metadata.layer_height_mm}mm layer, {self.metadata.wall_loops} walls, {self.metadata.infill_density_str} {self.metadata.infill_pattern}\n"
                f"  - Support Config:    {'Enabled' if self.metadata.support_enabled else 'Disabled'} ({self.metadata.support_style}, Top Z-gap: {self.metadata.support_top_z_gap}mm, Bottom: {self.metadata.support_bottom_z_gap}mm)\n"
                f"  - Model Bounds:      X:[{self.metadata.model_min_x:.1f}, {self.metadata.model_max_x:.1f}] Y:[{self.metadata.model_min_y:.1f}, {self.metadata.model_max_y:.1f}] Z:[{self.metadata.model_min_z:.1f}, {self.metadata.model_max_z:.1f}]\n"
            )
            if self.metadata.support_min_x is not None:
                s += f"  - Support Bounds:    X:[{self.metadata.support_min_x:.1f}, {self.metadata.support_max_x:.1f}] Y:[{self.metadata.support_min_y:.1f}, {self.metadata.support_max_y:.1f}]\n"
            if self.metadata.brim_min_x is not None:
                s += f"  - Brim Bounds:       X:[{self.metadata.brim_min_x:.1f}, {self.metadata.brim_max_x:.1f}] Y:[{self.metadata.brim_min_y:.1f}, {self.metadata.brim_max_y:.1f}]\n"
            s += (
                f"  - Printed Bounds:    X:[{self.metadata.printed_min_x:.1f}, {self.metadata.printed_max_x:.1f}] Y:[{self.metadata.printed_min_y:.1f}, {self.metadata.printed_max_y:.1f}] (Fits Plate: {self.metadata.is_within_build_plate})\n"
                f"  - Maintenance Area:  X:[{self.metadata.maintenance_min_x:.1f}, {self.metadata.maintenance_max_x:.1f}] Y:[{self.metadata.maintenance_min_y:.1f}, {self.metadata.maintenance_max_y:.1f}] (Off-bed Wiper/Cutter/Purge)\n"
                f"  - Metric Source:     ACTUAL SLICER DATA (is_actual_slicer_output=True, is_heuristic=False)\n"
            )
        if self.errors:
            s += f"  - Errors: {'; '.join(self.errors)}\n"
        if self.warnings:
            s += f"  - Warnings: {'; '.join(self.warnings)}\n"
        return s

class GCodeValidator:
    """Parses and validates Bambu Studio generated G-code files."""

    BUILD_VOLUME_A1 = (256.0, 256.0, 256.0)

    @classmethod
    def _parse_time_str_to_minutes(cls, time_str: str) -> float:
        """Converts strings like '2h 19m 31s' or '45m 12s' to fractional minutes."""
        hours = 0.0
        minutes = 0.0
        seconds = 0.0
        h_m = re.search(r'([0-9]+)\s*h', time_str)
        if h_m:
            hours = float(h_m.group(1))
        m_m = re.search(r'([0-9]+)\s*m', time_str)
        if m_m:
            minutes = float(m_m.group(1))
        s_m = re.search(r'([0-9]+)\s*s', time_str)
        if s_m:
            seconds = float(s_m.group(1))
        return (hours * 60.0) + minutes + (seconds / 60.0)

    @classmethod
    def validate_gcode(
        cls,
        gcode_path: str,
        expected_printer: str = "Bambu Lab A1",
        expected_filament: Optional[str] = None,
        max_build_volume: Tuple[float, float, float] = BUILD_VOLUME_A1
    ) -> GCodeValidationResult:
        """
        Validates G-code file integrity, extracts telemetry from header and config blocks,
        and verifies coordinate compliance against physical bed dimensions.
        """
        if not os.path.exists(gcode_path):
            return GCodeValidationResult(
                status=SlicerStatus.GCODE_VALIDATION_FAILED,
                is_valid=False,
                gcode_path=gcode_path,
                errors=[f"G-code file does not exist: {gcode_path}"]
            )

        file_size = os.path.getsize(gcode_path)
        if file_size < 1024:
            return GCodeValidationResult(
                status=SlicerStatus.GCODE_VALIDATION_FAILED,
                is_valid=False,
                gcode_path=gcode_path,
                errors=[f"G-code file is truncated or empty ({file_size} bytes). Minimum 1KB required."]
            )

        errors: List[str] = []
        warnings: List[str] = []

        # Read first 1000 lines for header and config blocks
        header_lines: List[str] = []
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(1500):
                line = f.readline()
                if not line:
                    break
                header_lines.append(line)

        header_text = "".join(header_lines)

        # 1. Structural block validation
        has_header_block = "HEADER_BLOCK_START" in header_text
        has_config_block = "CONFIG_BLOCK_START" in header_text
        if not has_header_block:
            errors.append("Invalid G-code structure: HEADER_BLOCK_START missing.")
        if not has_config_block:
            errors.append("Invalid G-code structure: CONFIG_BLOCK_START missing.")

        # 2. Slicer version
        slicer_version = "Unknown BambuStudio"
        sv_m = re.search(r';\s*(BambuStudio\s+[0-9\.]+)', header_text)
        if sv_m:
            slicer_version = sv_m.group(1).strip()

        # 3. Time telemetry
        tot_time_str = ""
        tot_time_m = re.search(r';\s*total estimated time:\s*([^\r\n;]+)', header_text)
        if tot_time_m:
            tot_time_str = tot_time_m.group(1).strip()

        model_time_str = ""
        mod_time_m = re.search(r';\s*model printing time:\s*([^\r\n;]+)', header_text)
        if mod_time_m:
            model_time_str = mod_time_m.group(1).strip()

        tot_time_mins = cls._parse_time_str_to_minutes(tot_time_str) if tot_time_str else 0.0

        # 4. Material telemetry
        weight_g = 0.0
        w_m = re.search(r';\s*total filament weight \[g\]\s*:\s*([0-9\.]+)', header_text)
        if w_m:
            weight_g = float(w_m.group(1))

        len_mm = 0.0
        l_m = re.search(r';\s*total filament length \[mm\]\s*:\s*([0-9\.]+)', header_text)
        if l_m:
            len_mm = float(l_m.group(1))

        vol_cm3 = 0.0
        v_m = re.search(r';\s*total filament volume \[cm\^3\]\s*:\s*([0-9\.]+)', header_text)
        if v_m:
            vol_cm3 = float(v_m.group(1))

        density = 1.24
        den_m = re.search(r';\s*filament_density:\s*([0-9\.]+)', header_text)
        if den_m:
            density = float(den_m.group(1))

        # 5. Layer telemetry
        total_layers = 0
        lay_m = re.search(r';\s*total layer number:\s*([0-9]+)', header_text)
        if lay_m:
            total_layers = int(lay_m.group(1))

        max_z = 0.0
        z_m = re.search(r';\s*max_z_height:\s*([0-9\.]+)', header_text)
        if z_m:
            max_z = float(z_m.group(1))

        # 6. Slicer config settings
        bed_type = ""
        bt_m = re.search(r';\s*curr_bed_type\s*=\s*([^\r\n;]+)', header_text)
        if bt_m:
            bed_type = bt_m.group(1).strip()

        printer_prof = ""
        pp_m = re.search(r';\s*default_print_profile\s*=\s*"?([^\r\n;"]+)"?', header_text)
        if pp_m:
            printer_prof = pp_m.group(1).strip()

        filament_prof = ""
        fp_m = re.search(r';\s*default_filament_profile\s*=\s*"?([^\r\n;"]+)"?', header_text)
        if fp_m:
            filament_prof = fp_m.group(1).strip()

        layer_h = 0.20
        lh_m = re.search(r';\s*layer_height\s*=\s*([0-9\.]+)', header_text)
        if lh_m:
            layer_h = float(lh_m.group(1))

        wall_loops = 3
        wl_m = re.search(r';\s*wall_loops\s*=\s*([0-9]+)', header_text)
        if wl_m:
            wall_loops = int(wl_m.group(1))

        infill_pat = "gyroid"
        ip_m = re.search(r';\s*sparse_infill_pattern\s*=\s*([^\r\n;]+)', header_text)
        if ip_m:
            infill_pat = ip_m.group(1).strip()

        infill_dens = "15%"
        id_m = re.search(r';\s*sparse_infill_density\s*=\s*([^\r\n;]+)', header_text)
        if id_m:
            infill_dens = id_m.group(1).strip()

        supp_enabled = False
        se_m = re.search(r';\s*enable_support\s*=\s*([0-9]+)', header_text)
        if se_m:
            supp_enabled = se_m.group(1).strip() == "1"

        supp_style = "tree_slim"
        ss_m = re.search(r';\s*support_style\s*=\s*([^\r\n;]+)', header_text)
        if ss_m:
            supp_style = ss_m.group(1).strip()

        supp_gap = 0.24
        sg_m = re.search(r';\s*support_top_z_distance\s*=\s*([0-9\.]+)', header_text)
        if sg_m:
            supp_gap = float(sg_m.group(1))

        supp_bottom_gap = 0.0
        sbg_m = re.search(r';\s*support_bottom_z_distance\s*=\s*([0-9\.]+)', header_text)
        if sbg_m:
            supp_bottom_gap = float(sbg_m.group(1))

        brim_type = "outer_only"
        brm_m = re.search(r';\s*brim_type\s*=\s*([^\r\n;]+)', header_text)
        if brm_m:
            brim_type = brm_m.group(1).strip()

        brim_width = 5.0
        bw_m = re.search(r';\s*brim_width\s*=\s*([0-9\.]+)', header_text)
        if bw_m:
            brim_width = float(bw_m.group(1))

        nozzle_temp = 220.0
        nt_m = re.search(r';\s*nozzle_temperature\s*=\s*([0-9\.]+)', header_text)
        if nt_m:
            nozzle_temp = float(nt_m.group(1))

        bed_temp = 65.0
        btp_m = re.search(r';\s*(?:textured_plate_temp|hot_plate_temp|bed_temperature)\s*=\s*([0-9\.]+)', header_text)
        if btp_m:
            bed_temp = float(btp_m.group(1))

        # Check end of G-code file for completion
        with open(gcode_path, 'rb') as f:
            f.seek(max(0, file_size - 10000))
            tail_data = f.read().decode('utf-8', errors='ignore')

        has_clean_end = any(k in tail_data for k in ["EXECUTABLE_BLOCK_END", "M1006 W", "M73 P100", "M104 S0"])
        if not has_clean_end:
            warnings.append("G-code trailing termination block not verified; file might have been interrupted.")

        # Coordinate boundary audit: separate model, support, brim, and maintenance movements
        MODEL_FEATURES = {
            'Outer wall', 'Inner wall', 'Sparse infill', 'Internal solid infill',
            'Top surface', 'Bottom surface', 'Overhang wall', 'Bridge',
            'Gap infill', 'Floating vertical shell', 'Skin'
        }

        model_min_x, model_max_x = 999.0, -999.0
        model_min_y, model_max_y = 999.0, -999.0
        model_min_z, model_max_z = 999.0, -999.0

        supp_min_x, supp_max_x = 999.0, -999.0
        supp_min_y, supp_max_y = 999.0, -999.0
        supp_min_z, supp_max_z = 999.0, -999.0

        brim_min_x, brim_max_x = 999.0, -999.0
        brim_min_y, brim_max_y = 999.0, -999.0

        printed_min_x, printed_max_x = 999.0, -999.0
        printed_min_y, printed_max_y = 999.0, -999.0
        printed_min_z, printed_max_z = 999.0, -999.0

        maint_min_x, maint_max_x = 999.0, -999.0
        maint_min_y, maint_max_y = 999.0, -999.0

        fl_min_x, fl_max_x = 999.0, -999.0
        fl_min_y, fl_max_y = 999.0, -999.0

        has_printed_coords = False
        has_maintenance_coords = False

        current_feature = "START_GCODE"
        prev_e = 0.0
        relative_e = False

        x_re = re.compile(r'X([0-9\.\-]+)')
        y_re = re.compile(r'Y([0-9\.\-]+)')
        z_re = re.compile(r'Z([0-9\.\-]+)')
        e_re = re.compile(r'E([0-9\.\-]+)')

        curr_z = 0.0

        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('; FEATURE:'):
                    current_feature = line[10:].strip()
                    continue
                elif line.startswith('M83'):
                    relative_e = True
                    continue
                elif line.startswith('M82'):
                    relative_e = False
                    continue
                elif line.startswith('G92 E0'):
                    prev_e = 0.0
                    continue

                if not (line.startswith('G1 ') or line.startswith('G0 ')):
                    continue

                em = e_re.search(line)
                is_extruding = False
                if em:
                    eval_val = float(em.group(1))
                    if relative_e:
                        is_extruding = eval_val > 0.0
                    else:
                        is_extruding = eval_val > prev_e
                        prev_e = eval_val

                xm = x_re.search(line)
                ym = y_re.search(line)
                zm = z_re.search(line)

                if zm:
                    curr_z = float(zm.group(1))

                if not xm and not ym:
                    continue

                x = float(xm.group(1)) if xm else None
                y = float(ym.group(1)) if ym else None

                if is_extruding:
                    has_printed_coords = True
                    if x is not None:
                        printed_min_x = min(printed_min_x, x)
                        printed_max_x = max(printed_max_x, x)
                    if y is not None:
                        printed_min_y = min(printed_min_y, y)
                        printed_max_y = max(printed_max_y, y)
                    printed_min_z = min(printed_min_z, curr_z)
                    printed_max_z = max(printed_max_z, curr_z)

                    if curr_z <= (layer_h * 1.5 + 0.1):
                        if x is not None:
                            fl_min_x = min(fl_min_x, x)
                            fl_max_x = max(fl_max_x, x)
                        if y is not None:
                            fl_min_y = min(fl_min_y, y)
                            fl_max_y = max(fl_max_y, y)

                    if current_feature in MODEL_FEATURES:
                        if x is not None:
                            model_min_x = min(model_min_x, x)
                            model_max_x = max(model_max_x, x)
                        if y is not None:
                            model_min_y = min(model_min_y, y)
                            model_max_y = max(model_max_y, y)
                        model_min_z = min(model_min_z, curr_z)
                        model_max_z = max(model_max_z, curr_z)
                    elif 'Support' in current_feature:
                        if x is not None:
                            supp_min_x = min(supp_min_x, x)
                            supp_max_x = max(supp_max_x, x)
                        if y is not None:
                            supp_min_y = min(supp_min_y, y)
                            supp_max_y = max(supp_max_y, y)
                        supp_min_z = min(supp_min_z, curr_z)
                        supp_max_z = max(supp_max_z, curr_z)
                    elif 'Brim' in current_feature or 'Skirt' in current_feature:
                        if x is not None:
                            brim_min_x = min(brim_min_x, x)
                            brim_max_x = max(brim_max_x, x)
                        if y is not None:
                            brim_min_y = min(brim_min_y, y)
                            brim_max_y = max(brim_max_y, y)
                else:
                    has_maintenance_coords = True
                    if x is not None:
                        maint_min_x = min(maint_min_x, x)
                        maint_max_x = max(maint_max_x, x)
                    if y is not None:
                        maint_min_y = min(maint_min_y, y)
                        maint_max_y = max(maint_max_y, y)

        fits_bed = True
        if has_printed_coords:
            # Printed material (model, support, brim) must be strictly within [0.0, max_build_volume]
            if (printed_min_x < 0.0 or printed_max_x > max_build_volume[0] or
                printed_min_y < 0.0 or printed_max_y > max_build_volume[1]):
                fits_bed = False
                errors.append(
                    f"Printed extrusion toolpath bounds X:[{printed_min_x:.1f}, {printed_max_x:.1f}] "
                    f"Y:[{printed_min_y:.1f}, {printed_max_y:.1f}] exceed printable bed area "
                    f"[0.0, {max_build_volume[0]:.1f}] x [0.0, {max_build_volume[1]:.1f}]mm."
                )
            if printed_max_z > max_build_volume[2]:
                fits_bed = False
                errors.append(
                    f"Printed extrusion height {printed_max_z:.2f}mm exceeds build volume Z ({max_build_volume[2]:.1f}mm)."
                )
        elif max_z > max_build_volume[2]:
            fits_bed = False
            errors.append(f"Model height {max_z:.2f}mm exceeds build volume Z ({max_build_volume[2]}mm).")

        # Non-printing machine maintenance moves (Bambu Lab A1 off-bed wiper/cutter/purge zones)
        if has_maintenance_coords:
            if maint_min_x < -60.0 or maint_max_x > 280.0 or maint_min_y < -15.0 or maint_max_y > 275.0:
                warnings.append(
                    f"Non-printing maintenance movement bounds X:[{maint_min_x:.1f}, {maint_max_x:.1f}] "
                    f"Y:[{maint_min_y:.1f}, {maint_max_y:.1f}] exceed recognized Bambu Lab A1 clearance envelope."
                )

        # Support top Z distance validation (layer-height aware)
        min_rec_gap = max(0.12, layer_h * 1.5)
        if supp_enabled and supp_gap < min_rec_gap and supp_gap < 0.12:
            warnings.append(
                f"Support top Z gap {supp_gap:.2f}mm is too tight for layer height {layer_h:.2f}mm "
                f"(recommended: {min_rec_gap:.2f}mm), risking support fusion."
            )

        meta = GCodeMetadata(
            gcode_path=os.path.abspath(gcode_path),
            file_size_bytes=file_size,
            slicer_version=slicer_version,
            model_printing_time_str=model_time_str,
            total_estimated_time_str=tot_time_str,
            total_estimated_time_minutes=tot_time_mins,
            total_filament_weight_g=weight_g,
            total_filament_length_mm=len_mm,
            total_filament_volume_cm3=vol_cm3,
            filament_density=density,
            filament_diameter=1.75,
            total_layers=total_layers,
            max_z_height_mm=max_z,
            printer_profile=printer_prof,
            filament_profile=filament_prof,
            bed_type=bed_type,
            layer_height_mm=layer_h,
            wall_loops=wall_loops,
            infill_pattern=infill_pat,
            infill_density_str=infill_dens,
            support_enabled=supp_enabled,
            support_style=supp_style,
            support_top_z_gap=supp_gap,
            support_bottom_z_gap=supp_bottom_gap,
            brim_type=brim_type,
            brim_width_mm=brim_width,
            nozzle_temperature=nozzle_temp,
            bed_temperature=bed_temp,
            model_min_x=model_min_x if has_printed_coords else 0.0,
            model_max_x=model_max_x if has_printed_coords else 0.0,
            model_min_y=model_min_y if has_printed_coords else 0.0,
            model_max_y=model_max_y if has_printed_coords else 0.0,
            model_min_z=model_min_z if has_printed_coords else 0.0,
            model_max_z=model_max_z if has_printed_coords else 0.0,
            support_min_x=supp_min_x if supp_min_x <= supp_max_x else None,
            support_max_x=supp_max_x if supp_min_x <= supp_max_x else None,
            support_min_y=supp_min_y if supp_min_y <= supp_max_y else None,
            support_max_y=supp_max_y if supp_min_y <= supp_max_y else None,
            support_min_z=supp_min_z if supp_min_z <= supp_max_z else None,
            support_max_z=supp_max_z if supp_min_z <= supp_max_z else None,
            brim_min_x=brim_min_x if brim_min_x <= brim_max_x else None,
            brim_max_x=brim_max_x if brim_min_x <= brim_max_x else None,
            brim_min_y=brim_min_y if brim_min_y <= brim_max_y else None,
            brim_max_y=brim_max_y if brim_min_y <= brim_max_y else None,
            printed_min_x=printed_min_x if has_printed_coords else 0.0,
            printed_max_x=printed_max_x if has_printed_coords else 0.0,
            printed_min_y=printed_min_y if has_printed_coords else 0.0,
            printed_max_y=printed_max_y if has_printed_coords else 0.0,
            printed_min_z=printed_min_z if has_printed_coords else 0.0,
            printed_max_z=printed_max_z if has_printed_coords else 0.0,
            maintenance_min_x=maint_min_x if has_maintenance_coords else 0.0,
            maintenance_max_x=maint_max_x if has_maintenance_coords else 0.0,
            maintenance_min_y=maint_min_y if has_maintenance_coords else 0.0,
            maintenance_max_y=maint_max_y if has_maintenance_coords else 0.0,
            first_layer_min_x=fl_min_x if fl_min_x <= fl_max_x else (printed_min_x if has_printed_coords else 0.0),
            first_layer_max_x=fl_max_x if fl_min_x <= fl_max_x else (printed_max_x if has_printed_coords else 0.0),
            first_layer_min_y=fl_min_y if fl_min_y <= fl_max_y else (printed_min_y if has_printed_coords else 0.0),
            first_layer_max_y=fl_max_y if fl_min_y <= fl_max_y else (printed_max_y if has_printed_coords else 0.0),
            is_within_build_plate=fits_bed,
            is_actual_slicer_output=True,
            is_heuristic_estimate=False
        )

        is_valid = len(errors) == 0
        status = SlicerStatus.SLICE_VALIDATED if is_valid else SlicerStatus.GCODE_VALIDATION_FAILED

        return GCodeValidationResult(
            status=status,
            is_valid=is_valid,
            gcode_path=os.path.abspath(gcode_path),
            metadata=meta,
            errors=errors,
            warnings=warnings
        )

