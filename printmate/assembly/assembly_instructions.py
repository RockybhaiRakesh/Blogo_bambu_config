"""
Assembly Instructions and Step-by-Step Guidance Generator module.
Synthesizes part connectivity graphs, sequential insertion vectors, angular keying alignments,
and adhesive/structural bonding recommendations into human- and machine-readable assembly manuals.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AssemblyStep:
    """Individual assembly action connecting two printed sub-components."""
    step_number: int
    base_component: str
    mating_component: str
    connector_architecture: str
    insertion_vector: str          # e.g., "-Z (0, 0, -1)"
    angular_keying_rule: str       # e.g., "Align flat chord of D-pin facing model front."
    adhesive_required: bool
    bonding_guidance: str
    verification_check: str

@dataclass
class AssemblyManual:
    """Complete technical assembly manual for multi-part 3D prints."""
    model_name: str
    total_components: int
    steps: List[AssemblyStep] = field(default_factory=list)
    bill_of_materials: List[Dict[str, Any]] = field(default_factory=list)
    general_safety_notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Renders complete assembly manual in GitHub Flavored Markdown."""
        bom_lines = []
        for item in self.bill_of_materials:
            bom_lines.append(
                f"| {item['id']} | **{item['part_name']}** | {item['dimensions']} | {item['role']} |"
            )
        bom_table = "\n".join(bom_lines)

        steps_blocks = []
        for s in self.steps:
            glue_badge = "🔴 ADHESIVE RECOMMENDED" if s.adhesive_required else "🟢 DRY PRESS-FIT / SLIP-FIT"
            steps_blocks.append(f"""### Step {s.step_number}: Connect `{s.mating_component}` to `{s.base_component}`

* **Joint Architecture:** {s.connector_architecture.upper()}
* **Bonding Class:** {glue_badge}
* **Insertion Direction:** `{s.insertion_vector}`
* **Angular Alignment Keying:** {s.angular_keying_rule}
* **Adhesive Advice:** {s.bonding_guidance}
* **Post-Assembly Verification:** {s.verification_check}
""")
        steps_rendered = "\n".join(steps_blocks)

        return f"""# Assembly Guide: {self.model_name}
**Prepared by:** PRINTMATE AI – Autonomous Assembly Engine  
**Total Printed Components:** {self.total_components}  

---

## 1. Bill of Materials (BOM) & Part Identification

| Part ID | Component Name | Dimensions ($X \\times Y \\times Z$) | Physical Role |
| :--- | :--- | :--- | :--- |
{bom_table}

---

## 2. Step-by-Step Assembly Sequence

{steps_rendered}

---

## 3. Engineering Best Practices
1. **Dry-Fit First:** Always test-mate parts without glue to ensure clearance before applying any chemical adhesive.
2. **De-burring:** If insertion feels stiff, gently scrape any brim residue or layer-line burrs around the socket mouth with a deburring tool.
3. **Cyanoacrylate (Super Glue) Usage:** For permanent bonding, apply a tiny drop to the base of the male pin, not the socket bottom, to prevent air compression from pushing glue onto visible outer seams.
"""

class AssemblyInstructionsGenerator:
    """Generates structured assembly instructions and connectivity graphs."""

    @classmethod
    def generate_instructions(
        cls,
        model_name: str,
        parts: List[str],
        connector_type: str = "d_shaped",
        output_path: Optional[str] = None
    ) -> AssemblyManual:
        """
        Builds the assembly sequence and writes the manual to disk if output_path is provided.
        """
        clean_parts = [os.path.basename(p) for p in parts]
        n_parts = len(clean_parts)

        bom: List[Dict[str, Any]] = []
        for idx, p in enumerate(clean_parts, start=1):
            role = "Pedestal / Mounting Base" if idx == 1 else f"Sub-Assembly Tier {idx}"
            bom.append({
                "id": f"P{idx:02d}",
                "part_name": p,
                "dimensions": "Derived from Slicer Geometry",
                "role": role
            })

        steps: List[AssemblyStep] = []
        for i in range(n_parts - 1):
            base_p = clean_parts[i]
            mating_p = clean_parts[i + 1]

            # Bonding advice based on connector type
            ctype = connector_type.lower()
            if ctype in ["cylindrical"]:
                glue_req = True
                bonding = "Apply 1-2 drops of Medium CA glue to prevent axial rotation."
                keying = "Rotate component until surface contour visually aligns before glue sets."
            elif ctype in ["d_shaped"]:
                glue_req = False
                bonding = "Mechanical flat chord provides angular lock; glue only needed for tensile locking."
                keying = "Align flat face of D-pin with flat recess in socket before pushing down."
            elif ctype in ["keyed"]:
                glue_req = False
                bonding = "Key spline locks rotation mechanically. Slip-fit is sufficient for static displays."
                keying = "Slide key into matching keyway slot."
            elif ctype in ["dual_pin", "asymmetric"]:
                glue_req = False
                bonding = "Dual pins prevent rotation completely. Press firmly until mating faces seat flush."
                keying = "Align both pins simultaneously; asymmetric sizes enforce unique 1-way mating."
            else:
                glue_req = False
                bonding = "Standard mechanical fit."
                keying = "Seat flush along split plane."

            steps.append(
                AssemblyStep(
                    step_number=i + 1,
                    base_component=base_p,
                    mating_component=mating_p,
                    connector_architecture=connector_type,
                    insertion_vector="-Z (Direct downward insertion)",
                    angular_keying_rule=keying,
                    adhesive_required=glue_req,
                    bonding_guidance=bonding,
                    verification_check=f"Confirm seam between `{base_p}` and `{mating_p}` has < 0.2mm visible gap."
                )
            )

        manual = AssemblyManual(
            model_name=model_name,
            total_components=n_parts,
            steps=steps,
            bill_of_materials=bom
        )

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(manual.to_markdown())

        return manual

