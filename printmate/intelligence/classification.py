"""
Classification engine for 3D model taxonomy.
Classifies models by scale, printable footprint, and geometric envelope.
NOTE: Semantic ML/Vision classification (e.g. human anatomy, jewelry recognition)
is slated for Phase 2/3 per the roadmap.
"""

from enum import Enum
from printmate.core.models import ModelInfo

class ScaleClass(str, Enum):
    MICRO = "Micro"                # < 25 mm
    MINIATURE = "Miniature"        # 25 mm - 65 mm
    STANDARD = "Standard"          # 65 mm - 180 mm
    LARGE = "Large"                # 180 mm - 256 mm
    OVERSIZED = "Oversized"        # > 256 mm (exceeds Bambu A1 build volume)

class ClassificationEngine:
    """Classifies model properties based on verifiable geometric dimensions."""

    @staticmethod
    def classify_scale(info: ModelInfo) -> ScaleClass:
        """
        Categorizes model into scale tiers based on bounding box extent.
        """
        max_dim = max(info.dim_x, info.dim_y, info.dim_z)

        if max_dim < 25.0:
            return ScaleClass.MICRO
        elif max_dim <= 65.0:
            return ScaleClass.MINIATURE
        elif max_dim <= 180.0:
            return ScaleClass.STANDARD
        elif max_dim <= 256.0:
            return ScaleClass.LARGE
        else:
            return ScaleClass.OVERSIZED

