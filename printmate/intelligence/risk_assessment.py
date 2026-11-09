"""
Risk assessment engine for 3D model printability.
Performs rule-based geometric risk checks for FDM printing on Bambu Lab A1.
"""

from typing import List, Dict, Any
from printmate.core.models import ModelInfo

class RiskAssessor:
    """Evaluates printing risks based on geometric characteristics."""

    @staticmethod
    def assess(info: ModelInfo) -> List[str]:
        """
        Runs geometric risk heuristics against the model info.
        
        Args:
            info: ModelInfo dataclass containing geometry metrics.
            
        Returns:
            List of detected risk descriptions.
        """
        risks: List[str] = []

        # Miniature scale risk (fragile limbs / support fusing)
        if info.dim_z < 65.0:
            risks.append(
                f"Miniature Scale Risk: Model height ({info.dim_z:.1f} mm) is under 65mm. "
                "Delicate features (hands, fingers, jewelry) require increased Z air-gap (>=0.24mm) "
                "to prevent permanent support fusion."
            )

        # Aspect ratio / bed slinger tipping risk
        min_base = min(info.dim_x, info.dim_y)
        if min_base > 0:
            aspect_ratio = info.dim_z / min_base
            if aspect_ratio > 3.0:
                risks.append(
                    f"Tipping Risk: Aspect ratio ({aspect_ratio:.2f}) is high. "
                    "Y-axis bed movement may knock over tall narrow structure without a wide brim (>=5mm)."
                )

        # Watertightness / non-manifold risk
        if not info.is_watertight:
            risks.append(
                "Mesh Integrity Warning: Model has open boundaries or non-manifold edges. "
                "Slicer may fail to slice internal infill correctly if not repaired."
            )

        # High polygon count strain
        if info.faces > 1_000_000:
            risks.append(
                f"High Complexity Warning: Mesh has {info.faces:,} triangles (>1M). "
                "Bambu Studio may take longer to slice and preview."
            )

        return risks

