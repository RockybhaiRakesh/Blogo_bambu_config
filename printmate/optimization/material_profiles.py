"""
Material and filament speed profiles for Bambu Lab A1 (0.4mm nozzle).
Preserves verified mechanical parameters for zero-breakage printing.
"""

from typing import Dict, Any

class MaterialProfiles:
    """Provides material-specific speeds, cooling, and air-gap compensations."""

    PROFILES: Dict[str, Dict[str, Any]] = {
        "pla_basic": {
            "outer_wall_speed": ["55"],
            "inner_wall_speed": ["120"],
            "support_top_z_distance": "0.24",
            "support_object_xy_distance": "0.60",
        },
        "pla_matte": {
            "outer_wall_speed": ["55"],
            "inner_wall_speed": ["120"],
            "support_top_z_distance": "0.24",
            "support_object_xy_distance": "0.60",
        },
        "pla_silk": {
            # Silk PLA swells slightly and is prone to layer tearing; slower outer wall & larger gap
            "outer_wall_speed": ["45"],
            "inner_wall_speed": ["100"],
            "support_top_z_distance": "0.26",
            "support_object_xy_distance": "0.65",
        },
        "pla_silk_plus_gold": {
            # Silk+ Gold: 208°C anti-sag, 40mm/s wall speed for pure metallic luster, and 0.26mm support gap
            "outer_wall_speed": ["40"],
            "inner_wall_speed": ["80"],
            "nozzle_temperature": ["208"],
            "support_top_z_distance": "0.26",
            "support_object_xy_distance": "0.65",
        },
        "petg": {
            # PETG adheres very aggressively to support interfaces; requires larger release air gap
            "outer_wall_speed": ["40"],
            "inner_wall_speed": ["90"],
            "support_top_z_distance": "0.28",
            "support_object_xy_distance": "0.70",
        }
    }

    @classmethod
    def get_profile(cls, material_name: str) -> Dict[str, Any]:
        """
        Retrieves filament-specific slicer parameters. Defaults to pla_basic if unknown.
        """
        key = material_name.lower().replace("-", "_")
        return cls.PROFILES.get(key, cls.PROFILES["pla_basic"]).copy()

