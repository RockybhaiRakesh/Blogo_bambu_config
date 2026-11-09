"""
Print strategy optimizer module.
Constructs verified Bambu Studio configuration overrides matching model requirements.
Integrates Phase 5 SettingsEngine for multi-objective optimization.
"""

from typing import Dict, Any, Optional
from printmate.core.models import ModelInfo
from printmate.optimization.material_profiles import MaterialProfiles

class StrategyOptimizer:
    """Optimizes Bambu Studio slicer profiles for zero-breakage printing."""

    @staticmethod
    def build_slicer_overrides(
        mode: str = "single",
        filament: str = "pla_basic",
        info: Optional[ModelInfo] = None,
        objective: Optional[str] = None,
        has_connectors: bool = False
    ) -> Dict[str, Any]:
        """
        Builds the complete dictionary of JSON parameters to inject into Bambu project_settings.config.
        Preserves 100% backward compatibility with Phase 0-4 tests while supporting Phase 5 objectives.
        """
        if objective is not None:
            from printmate.optimization.settings_engine import SettingsEngine, OptimizationObjective
            obj_enum = OptimizationObjective(objective) if objective in [o.value for o in OptimizationObjective] else OptimizationObjective.BALANCED_QUALITY
            settings = SettingsEngine.optimize(
                mesh_or_info=info,
                objective=obj_enum,
                filament_id=filament,
                has_connectors=has_connectors,
                is_split_flat=(mode == "split")
            )
            config = settings.to_slicer_overrides()
            if not isinstance(config.get("nozzle_diameter"), list):
                config["nozzle_diameter"] = [str(config.get("nozzle_diameter", "0.4"))]
            return config

        # Standard baseline configuration (Phase 0-4 verified defaults)
        config: Dict[str, Any] = {
            "printer_model": "Bambu Lab A1",
            "nozzle_diameter": ["0.4"],
            "layer_height": "0.12" if mode == "single" else "0.16",
            "wall_loops": "4" if has_connectors else "3",
            "sparse_infill_pattern": "gyroid",
            "sparse_infill_density": "15%",
            "brim_type": "outer_only",
            "brim_width": "5",
            "seam_position": "back",
            "wall_generator": "arachne",
        }

        # Safe Tree Slim supports enabled by default for zero-breakage printing
        config.update({
            "enable_support": "1",
            "support_type": "tree(auto)",
            "support_style": "tree_slim",
            "support_top_z_distance": "0.24",
            "support_object_xy_distance": "0.60",
            "support_interface_top_layers": "2",
            "support_threshold_angle": "25",
            "tree_support_branch_angle": "45",
            "tree_support_branch_diameter": "2",
            "tree_support_branch_diameter_angle": "5",
            "tree_support_branch_distance": "5",
            "tree_support_wall_count": "-1",
        })

        if mode != "single":
            config.update({
                "brim_type": "outer_only",
                "brim_width": "5"
            })

        mat_settings = MaterialProfiles.get_profile(filament)
        config.update(mat_settings)
        return config

