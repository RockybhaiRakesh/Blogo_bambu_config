"""
Printer Profile Architecture module.
Provides versioned, provenance-tracked 3D printer hardware profiles.
Stores mechanical limits, kinematic constraints, thermal envelopes, build volumes,
and nozzle/enclosure capabilities for enterprise print preparation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional

class ProfileProvenance(str, Enum):
    """Origin and validation status of machine and material profiles."""
    MANUFACTURER_VERIFIED = "MANUFACTURER_VERIFIED"  # Official OEM technical specification
    USER_CALIBRATED = "USER_CALIBRATED"              # Empirically measured by operator in Phase 4
    THEORETICAL_DEFAULT = "THEORETICAL_DEFAULT"      # Algorithmic / heuristic baseline

@dataclass
class PrinterProfile:
    """Hardware capability and physical envelope of a 3D printer."""
    id: str
    name: str
    manufacturer: str
    build_volume_x: float
    build_volume_y: float
    build_volume_z: float
    default_nozzle_diameter: float = 0.4
    available_nozzle_diameters: List[float] = field(default_factory=lambda: [0.2, 0.4, 0.6, 0.8])
    max_nozzle_temp: float = 300.0
    max_bed_temp: float = 100.0
    has_enclosure: bool = False
    has_hardened_nozzle: bool = False
    is_direct_drive: bool = True
    max_acceleration_mm_s2: float = 10000.0
    default_bed_type: str = "Textured PEI Plate"
    supported_materials: List[str] = field(default_factory=lambda: [
        "pla_basic", "pla_plus", "pla_matte", "pla_silk", "petg", "tpu"
    ])
    provenance: ProfileProvenance = ProfileProvenance.THEORETICAL_DEFAULT
    notes: str = ""

    @property
    def build_volume(self) -> Tuple[float, float, float]:
        return (self.build_volume_x, self.build_volume_y, self.build_volume_z)

    def supports_material(self, material_id: str) -> bool:
        """Checks if machine hardware safely accommodates the given material."""
        mat_clean = material_id.lower().replace("-", "_")
        return mat_clean in [m.lower().replace("-", "_") for m in self.supported_materials]

    def is_material_supported(self, material_id: str) -> bool:
        """Alias for supports_material."""
        return self.supports_material(material_id)

    def summary(self) -> str:
        enc_str = "Enclosed" if self.has_enclosure else "Open-Frame"
        noz_str = "Hardened Steel" if self.has_hardened_nozzle else "Standard Brass/Stainless"
        return (
            f"PrinterProfile [{self.name} ({self.manufacturer})]: "
            f"Build: {self.build_volume_x:.0f}x{self.build_volume_y:.0f}x{self.build_volume_z:.0f}mm | "
            f"{enc_str} | Nozzle: {self.default_nozzle_diameter}mm ({noz_str}) | "
            f"Max Temps: {self.max_nozzle_temp:.0f}°C Nozzle, {self.max_bed_temp:.0f}°C Bed [{self.provenance.value}]"
        )

class PrinterProfileRegistry:
    """Enterprise registry of validated and extensible 3D printer profiles."""

    _REGISTRY: Dict[str, PrinterProfile] = {
        # 1. Target Validated Hardware: Bambu Lab A1
        "bambu_lab_a1": PrinterProfile(
            id="bambu_lab_a1",
            name="Bambu Lab A1",
            manufacturer="Bambu Lab",
            build_volume_x=256.0,
            build_volume_y=256.0,
            build_volume_z=256.0,
            default_nozzle_diameter=0.4,
            max_nozzle_temp=300.0,
            max_bed_temp=100.0,
            has_enclosure=False,
            has_hardened_nozzle=False,
            is_direct_drive=True,
            max_acceleration_mm_s2=10000.0,
            default_bed_type="Textured PEI Plate",
            supported_materials=["pla_basic", "pla_plus", "pla_matte", "pla_silk", "petg", "tpu"],
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Primary target machine. Open-bed Cartesian bedslinger with direct drive active flow compensation."
        ),

        # 2. Bambu Lab X1-Carbon
        "bambu_lab_x1_carbon": PrinterProfile(
            id="bambu_lab_x1_carbon",
            name="Bambu Lab X1-Carbon",
            manufacturer="Bambu Lab",
            build_volume_x=256.0,
            build_volume_y=256.0,
            build_volume_z=256.0,
            default_nozzle_diameter=0.4,
            max_nozzle_temp=300.0,
            max_bed_temp=120.0,
            has_enclosure=True,
            has_hardened_nozzle=True,
            is_direct_drive=True,
            max_acceleration_mm_s2=20000.0,
            default_bed_type="Textured PEI Plate",
            supported_materials=[
                "pla_basic", "pla_plus", "pla_matte", "pla_silk", "petg", "abs", "asa", "tpu",
                "nylon", "pc", "pla_cf", "petg_cf", "pa_cf"
            ],
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Fully enclosed CoreXY with chamber monitoring, micro-lidar, and hardened extruder."
        ),

        # 3. Prusa MK4
        "prusa_mk4": PrinterProfile(
            id="prusa_mk4",
            name="Prusa MK4",
            manufacturer="Prusa Research",
            build_volume_x=250.0,
            build_volume_y=210.0,
            build_volume_z=220.0,
            default_nozzle_diameter=0.4,
            max_nozzle_temp=290.0,
            max_bed_temp=120.0,
            has_enclosure=False,
            has_hardened_nozzle=False,
            is_direct_drive=True,
            max_acceleration_mm_s2=4000.0,
            default_bed_type="Smooth PEI Sheet",
            supported_materials=["pla_basic", "pla_plus", "pla_matte", "pla_silk", "petg", "tpu", "asa"],
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Open-bed Nextruder direct-drive with loadcell bed leveling."
        ),

        # 4. Creality K1
        "creality_k1": PrinterProfile(
            id="creality_k1",
            name="Creality K1",
            manufacturer="Creality",
            build_volume_x=220.0,
            build_volume_y=220.0,
            build_volume_z=250.0,
            default_nozzle_diameter=0.4,
            max_nozzle_temp=300.0,
            max_bed_temp=100.0,
            has_enclosure=True,
            has_hardened_nozzle=False,
            is_direct_drive=True,
            max_acceleration_mm_s2=20000.0,
            default_bed_type="Smooth PEI Sheet",
            supported_materials=["pla_basic", "pla_plus", "pla_matte", "pla_silk", "petg", "abs", "asa", "tpu"],
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Enclosed high-speed CoreXY."
        ),

        # 5. Creality Ender 3 V3
        "creality_ender_3_v3": PrinterProfile(
            id="creality_ender_3_v3",
            name="Creality Ender 3 V3",
            manufacturer="Creality",
            build_volume_x=220.0,
            build_volume_y=220.0,
            build_volume_z=250.0,
            default_nozzle_diameter=0.4,
            max_nozzle_temp=300.0,
            max_bed_temp=100.0,
            has_enclosure=False,
            has_hardened_nozzle=False,
            is_direct_drive=True,
            max_acceleration_mm_s2=8000.0,
            default_bed_type="Textured PEI Plate",
            supported_materials=["pla_basic", "pla_plus", "pla_matte", "pla_silk", "petg", "tpu"],
            provenance=ProfileProvenance.THEORETICAL_DEFAULT,
            notes="Open-bed CoreXZ architecture with direct Sprite extruder."
        ),

        # 6. Anycubic Kobra 2
        "anycubic_kobra_2": PrinterProfile(
            id="anycubic_kobra_2",
            name="Anycubic Kobra 2",
            manufacturer="Anycubic",
            build_volume_x=220.0,
            build_volume_y=220.0,
            build_volume_z=250.0,
            default_nozzle_diameter=0.4,
            max_nozzle_temp=260.0,
            max_bed_temp=110.0,
            has_enclosure=False,
            has_hardened_nozzle=False,
            is_direct_drive=True,
            max_acceleration_mm_s2=3000.0,
            default_bed_type="Textured PEI Plate",
            supported_materials=["pla_basic", "pla_plus", "pla_matte", "petg", "tpu"],
            provenance=ProfileProvenance.THEORETICAL_DEFAULT,
            notes="Entry level open-bed bedslinger."
        ),
    }

    @classmethod
    def get_profile(cls, name_or_id: str = "Bambu Lab A1") -> PrinterProfile:
        """Retrieves matching printer profile, or defaults safely to Bambu Lab A1."""
        clean_key = name_or_id.lower().replace(" ", "_").replace("-", "_")
        if clean_key in cls._REGISTRY:
            return cls._REGISTRY[clean_key]

        # Search by display name
        for p in cls._REGISTRY.values():
            if p.name.lower() == name_or_id.lower():
                return p

        # Fallback to Bambu Lab A1
        return cls._REGISTRY["bambu_lab_a1"]

    @classmethod
    def register_profile(cls, profile: PrinterProfile, overwrite: bool = False) -> None:
        """Registers a custom or calibrated printer profile."""
        key = profile.id.lower().replace(" ", "_").replace("-", "_")
        if key in cls._REGISTRY and not overwrite:
            raise ValueError(f"Printer profile '{profile.id}' already exists. Pass overwrite=True to update.")
        cls._REGISTRY[key] = profile

    @classmethod
    def list_printers(cls) -> List[PrinterProfile]:
        """Returns all registered printer profiles."""
        return list(cls._REGISTRY.values())
