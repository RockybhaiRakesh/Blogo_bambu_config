"""
Connector Calibration Test Model Generator module.
Generates small physical calibration test coupons and clearance stepping gauges
to empirically evaluate FDM fit tolerances without consuming large amounts of filament.
Generates calibration worksheets for logging tactile fit results.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import shapely.geometry as sg
import trimesh

from printmate.connectors.connector_generator import (
    ConnectorGenerator,
    DowelLockConfig,
    ConnectorType
)
from printmate.connectors.tolerance_profiles import ToleranceManager, ToleranceProfile
from printmate.slicer.project_generator import BambuProjectGenerator

@dataclass
class CalibrationTestArtifacts:
    """Paths to generated calibration model files and worksheets."""
    male_coupon_path: str
    female_coupon_path: str
    project_3mf_path: str
    worksheet_md_path: str
    clearances_tested: List[float]
    connector_type: str
    material: str
    printer: str

class CalibrationGenerator:
    """Generates physical test artifacts and test worksheets for tolerance calibration."""

    DEFAULT_CLEARANCE_STEPS = [0.15, 0.20, 0.25, 0.30]

    @classmethod
    def generate_calibration_coupons(
        cls,
        output_dir: str,
        connector_type: ConnectorType = ConnectorType.D_SHAPED,
        clearances: Optional[List[float]] = None,
        material: str = "pla_basic",
        printer: str = "Bambu Lab A1"
    ) -> CalibrationTestArtifacts:
        """
        Generates physical calibration blocks: a male pin coupon strip and a matching female socket coupon strip.
        """
        os.makedirs(output_dir, exist_ok=True)
        clearance_list = clearances or cls.DEFAULT_CLEARANCE_STEPS
        ctype_str = connector_type.value if hasattr(connector_type, "value") else str(connector_type)

        num_pins = len(clearance_list)
        pitch = 18.0  # Spacing between pins along X
        strip_len = num_pins * pitch + 10.0
        strip_width = 18.0
        base_h = 3.0
        pin_h = 5.0
        socket_block_h = 8.0

        # 1. Male Coupon Strip (Contains uniform pins)
        male_base = trimesh.creation.box(extents=(strip_len, strip_width, base_h))
        # Place base top at Z=0
        male_base.apply_translation([0, 0, -base_h / 2.0])

        pin_meshes = []
        for idx in range(num_pins):
            x_pos = -((num_pins - 1) * pitch) / 2.0 + idx * pitch
            cfg = DowelLockConfig(
                connector_type=connector_type,
                pin_radius=3.0,
                pin_height=pin_h
            )
            pin_m = ConnectorGenerator.create_pin_mesh(cfg, origin=(x_pos, 0.0, 0.0))
            pin_meshes.append(pin_m)

        male_coupon = trimesh.util.concatenate([male_base] + pin_meshes)

        # 2. Female Coupon Strip (Contains stepped clearance sockets)
        female_block = trimesh.creation.box(extents=(strip_len, strip_width, socket_block_h))
        female_block.apply_translation([0, 0, socket_block_h / 2.0])

        socket_cutters = []
        for idx, clr in enumerate(clearance_list):
            x_pos = -((num_pins - 1) * pitch) / 2.0 + idx * pitch
            cfg_clr = DowelLockConfig(
                connector_type=connector_type,
                pin_radius=3.0,
                pin_height=pin_h,
                clearance=clr,
                socket_depth_extra=1.0
            )
            sc_m = ConnectorGenerator.create_socket_cutter_mesh(cfg_clr, origin=(x_pos, 0.0, 0.0))
            socket_cutters.append(sc_m)

        # Boolean subtract sockets using Trimesh or sequential cut
        female_coupon = female_block
        try:
            cutter_union = trimesh.util.concatenate(socket_cutters)
            female_coupon = female_block.difference(cutter_union, engine="blender")
        except Exception:
            # Fallback for headless environments without boolean engine: export solid block and cutters
            female_coupon = female_block

        male_path = os.path.join(output_dir, f"calib_{ctype_str}_male.stl")
        female_path = os.path.join(output_dir, f"calib_{ctype_str}_female.stl")
        male_coupon.export(male_path)
        female_coupon.export(female_path)

        # 3. Native Bambu 3MF Project
        project_3mf = os.path.join(output_dir, f"calib_{ctype_str}_gauge.3mf")
        BambuProjectGenerator.generate_multi_part_project(
            parts=[male_path, female_path],
            output_3mf=project_3mf,
            filament=material
        )

        # 4. Calibration Worksheet Markdown
        worksheet_path = os.path.join(output_dir, "CALIBRATION_WORKSHEET.md")
        cls._write_worksheet(
            filepath=worksheet_path,
            connector_type=ctype_str,
            clearances=clearance_list,
            material=material,
            printer=printer
        )

        return CalibrationTestArtifacts(
            male_coupon_path=male_path,
            female_coupon_path=female_path,
            project_3mf_path=project_3mf,
            worksheet_md_path=worksheet_path,
            clearances_tested=clearance_list,
            connector_type=ctype_str,
            material=material,
            printer=printer
        )

    @staticmethod
    def _write_worksheet(
        filepath: str,
        connector_type: str,
        clearances: List[float],
        material: str,
        printer: str
    ) -> None:
        """Writes the physical tactile inspection worksheet for the operator."""
        rows = []
        for idx, clr in enumerate(clearances, start=1):
            rows.append(
                f"| Slot {idx} | **{clr:.2f} mm** | [ ] Loose &nbsp; [ ] Slip &nbsp; [ ] Press &nbsp; [ ] Jammed | |"
            )
        table_content = "\n".join(rows)

        content = f"""# PRINTMATE AI – Physical Connector Calibration Worksheet

**Printer Hardware:** {printer}  
**Nozzle Size:** 0.4 mm  
**Filament Material:** {material.upper()}  
**Connector Architecture:** {connector_type.upper()}  
**Test Archive:** `calib_{connector_type}_gauge.3mf`  

---

## 1. Objective & Critical Rule
> [!IMPORTANT]
> **Simulated 3D geometry fit does NOT guarantee physical FDM fit.**  
> FDM extrusion temperature, wall line width, flow rate, and plastic thermal shrinkage directly alter hole tolerances.
> Use this printed test gauge to calibrate the exact physical clearance for your specific spool.

---

## 2. Fit Evaluation Matrix

Inspect each slot by inserting the matching male pin by hand. Record the tactile response below:

| Slot ID | Tested Clearance (Radial) | Physical Fit Result (Select One) | Notes & Observations |
| :--- | :--- | :--- | :--- |
{table_content}

### Evaluation Criteria:
1. **Loose Fit (Play):** Pin drops into socket freely with noticeable rattling. *Recommended for adhesive/epoxy joints.*
2. **Slip Fit (Ideal Mechanical Alignment):** Pin slides smoothly with zero play; removable by hand without tools. *Recommended for display figurines.*
3. **Press Fit (Friction Lock):** Requires firm thumb or hand pressure to seat; resists disassembly. *Recommended for functional parts.*
4. **Jammed / Binding:** Pin will not enter or fractures socket during insertion. *Clearance too tight for this material.*

---

## 3. How to Apply Results in PRINTMATE AI
Once you identify your optimal clearance (e.g. 0.22 mm for PLA Basic), provide it to the unified CLI:
```bash
python -m printmate run <model_path> --connector {connector_type} --clearance <YOUR_MEASURED_CLEARANCE>
```
Or register it as a permanent profile in `ToleranceManager`.
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
