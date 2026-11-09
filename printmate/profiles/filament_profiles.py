"""
Filament Profile Management module.
Maintains comprehensive, brand-specific and material-specific filament profiles.
Governs thermal envelopes, maximum volumetric flow limits, cooling rules, retraction kinematics,
drying protocols, and engineering constraints (enclosure requirement, abrasive wear).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from printmate.profiles.printer_profiles import ProfileProvenance

class MaterialCategory(str, Enum):
    PLA_BASIC = "pla_basic"
    PLA_PLUS = "pla_plus"
    PLA_MATTE = "pla_matte"
    PLA_SILK = "pla_silk"
    PETG = "petg"
    ABS = "abs"
    ASA = "asa"
    TPU = "tpu"
    NYLON = "nylon"
    PC = "pc"
    PLA_CF = "pla_cf"
    PETG_CF = "petg_cf"
    PA_CF = "pa_cf"

@dataclass
class FilamentProfile:
    """Comprehensive material specification for slicer parameter injection."""
    id: str
    brand: str
    material_name: str
    category: MaterialCategory
    density_g_cm3: float = 1.24
    nozzle_temp_min: float = 200.0
    nozzle_temp_max: float = 240.0
    nozzle_temp_recommended: float = 220.0
    bed_temp_min: float = 45.0
    bed_temp_max: float = 65.0
    bed_temp_recommended: float = 55.0
    max_volumetric_speed_mm3_s: float = 21.0
    outer_wall_speed_mm_s: float = 60.0
    inner_wall_speed_mm_s: float = 120.0
    sparse_infill_speed_mm_s: float = 150.0
    travel_speed_mm_s: float = 250.0
    cooling_fan_min_pct: float = 80.0
    cooling_fan_max_pct: float = 100.0
    fan_off_first_layers: int = 1
    retraction_length_mm: float = 0.8
    retraction_speed_mm_s: float = 30.0
    flow_ratio: float = 0.98
    drying_temp_c: Optional[float] = None
    drying_duration_hrs: Optional[float] = None
    enclosure_required: bool = False
    is_abrasive: bool = False  # Requires hardened steel nozzle
    moisture_sensitive: bool = False
    provenance: ProfileProvenance = ProfileProvenance.THEORETICAL_DEFAULT
    notes: str = ""

    def summary(self) -> str:
        enc = "Enclosure REQ" if self.enclosure_required else "Open-Bed OK"
        abr = "ABRASIVE (Hardened Nozzle REQ)" if self.is_abrasive else "Non-Abrasive"
        return (
            f"FilamentProfile [{self.brand} {self.material_name}]: "
            f"Nozzle {self.nozzle_temp_recommended:.0f}°C ({self.nozzle_temp_min:.0f}-{self.nozzle_temp_max:.0f}°C), "
            f"Bed {self.bed_temp_recommended:.0f}°C | Max Flow {self.max_volumetric_speed_mm3_s:.1f}mm³/s | "
            f"{enc} | {abr} [{self.provenance.value}]"
        )

class FilamentProfileRegistry:
    """Enterprise registry of validated multi-brand filament profiles."""

    _REGISTRY: Dict[str, FilamentProfile] = {
        # 1. Bambu Lab PLA Basic
        "bambu_pla_basic": FilamentProfile(
            id="bambu_pla_basic",
            brand="Bambu Lab",
            material_name="PLA Basic",
            category=MaterialCategory.PLA_BASIC,
            density_g_cm3=1.24,
            nozzle_temp_min=190.0,
            nozzle_temp_max=240.0,
            nozzle_temp_recommended=220.0,
            bed_temp_min=35.0,
            bed_temp_max=65.0,
            bed_temp_recommended=55.0,
            max_volumetric_speed_mm3_s=21.0,
            outer_wall_speed_mm_s=60.0,
            inner_wall_speed_mm_s=120.0,
            sparse_infill_speed_mm_s=180.0,
            cooling_fan_min_pct=80.0,
            cooling_fan_max_pct=100.0,
            fan_off_first_layers=1,
            retraction_length_mm=0.8,
            retraction_speed_mm_s=30.0,
            flow_ratio=0.98,
            drying_temp_c=55.0,
            drying_duration_hrs=8.0,
            enclosure_required=False,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="OEM high-speed PLA formulation for Bambu A1 and X1."
        ),

        # 2. Bambu Lab PLA Matte
        "bambu_pla_matte": FilamentProfile(
            id="bambu_pla_matte",
            brand="Bambu Lab",
            material_name="PLA Matte",
            category=MaterialCategory.PLA_MATTE,
            density_g_cm3=1.31,
            nozzle_temp_min=190.0,
            nozzle_temp_max=240.0,
            nozzle_temp_recommended=220.0,
            bed_temp_min=35.0,
            bed_temp_max=65.0,
            bed_temp_recommended=55.0,
            max_volumetric_speed_mm3_s=16.0,
            outer_wall_speed_mm_s=55.0,
            inner_wall_speed_mm_s=110.0,
            sparse_infill_speed_mm_s=160.0,
            cooling_fan_min_pct=80.0,
            cooling_fan_max_pct=100.0,
            fan_off_first_layers=1,
            flow_ratio=0.98,
            enclosure_required=False,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Matte diffuse finish with micro-texture; slightly lower volumetric speed than Basic."
        ),

        # 3. Bambu Lab PLA Silk
        "bambu_pla_silk": FilamentProfile(
            id="bambu_pla_silk",
            brand="Bambu Lab",
            material_name="PLA Silk",
            category=MaterialCategory.PLA_SILK,
            density_g_cm3=1.22,
            nozzle_temp_min=205.0,
            nozzle_temp_max=235.0,
            nozzle_temp_recommended=225.0,
            bed_temp_min=35.0,
            bed_temp_max=65.0,
            bed_temp_recommended=55.0,
            max_volumetric_speed_mm3_s=12.0,
            outer_wall_speed_mm_s=45.0,
            inner_wall_speed_mm_s=90.0,
            sparse_infill_speed_mm_s=130.0,
            cooling_fan_min_pct=80.0,
            cooling_fan_max_pct=100.0,
            fan_off_first_layers=1,
            flow_ratio=0.98,
            enclosure_required=False,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Requires slower outer wall speeds (45mm/s) to achieve high-luster reflective sheen and avoid tearing."
        ),

        # 4. eSUN PLA+
        "esun_pla_plus": FilamentProfile(
            id="esun_pla_plus",
            brand="eSUN",
            material_name="PLA+",
            category=MaterialCategory.PLA_PLUS,
            density_g_cm3=1.24,
            nozzle_temp_min=205.0,
            nozzle_temp_max=225.0,
            nozzle_temp_recommended=215.0,
            bed_temp_min=55.0,
            bed_temp_max=65.0,
            bed_temp_recommended=60.0,
            max_volumetric_speed_mm3_s=15.0,
            outer_wall_speed_mm_s=50.0,
            inner_wall_speed_mm_s=100.0,
            cooling_fan_min_pct=100.0,
            cooling_fan_max_pct=100.0,
            flow_ratio=0.98,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Modified impact-resistant PLA with improved elongation at break."
        ),

        # 5. Bambu Lab PETG Basic
        "bambu_petg_basic": FilamentProfile(
            id="bambu_petg_basic",
            brand="Bambu Lab",
            material_name="PETG Basic",
            category=MaterialCategory.PETG,
            density_g_cm3=1.27,
            nozzle_temp_min=230.0,
            nozzle_temp_max=260.0,
            nozzle_temp_recommended=250.0,
            bed_temp_min=65.0,
            bed_temp_max=85.0,
            bed_temp_recommended=75.0,
            max_volumetric_speed_mm3_s=13.0,
            outer_wall_speed_mm_s=45.0,
            inner_wall_speed_mm_s=90.0,
            sparse_infill_speed_mm_s=140.0,
            cooling_fan_min_pct=40.0,
            cooling_fan_max_pct=70.0,
            fan_off_first_layers=3,
            retraction_length_mm=1.0,
            retraction_speed_mm_s=25.0,
            flow_ratio=0.98,
            drying_temp_c=65.0,
            drying_duration_hrs=8.0,
            moisture_sensitive=True,
            enclosure_required=False,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Ductile, chemical and weather resistant. Reduced fan speed preserves layer bonding."
        ),

        # 6. Polymaker PolyLite PETG
        "polymaker_polylite_petg": FilamentProfile(
            id="polymaker_polylite_petg",
            brand="Polymaker",
            material_name="PolyLite PETG",
            category=MaterialCategory.PETG,
            density_g_cm3=1.25,
            nozzle_temp_min=230.0,
            nozzle_temp_max=240.0,
            nozzle_temp_recommended=235.0,
            bed_temp_min=70.0,
            bed_temp_max=80.0,
            bed_temp_recommended=75.0,
            max_volumetric_speed_mm3_s=12.0,
            flow_ratio=0.98,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Tight tolerance standard PETG."
        ),

        # 7. Bambu Lab ABS
        "bambu_abs": FilamentProfile(
            id="bambu_abs",
            brand="Bambu Lab",
            material_name="ABS",
            category=MaterialCategory.ABS,
            density_g_cm3=1.05,
            nozzle_temp_min=240.0,
            nozzle_temp_max=270.0,
            nozzle_temp_recommended=260.0,
            bed_temp_min=90.0,
            bed_temp_max=110.0,
            bed_temp_recommended=100.0,
            max_volumetric_speed_mm3_s=15.0,
            cooling_fan_min_pct=10.0,
            cooling_fan_max_pct=25.0,
            fan_off_first_layers=5,
            enclosure_required=True,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="High heat deflection (87°C); REQUIRES ENCLOSURE to prevent warping and delamination."
        ),

        # 8. Bambu Lab ASA
        "bambu_asa": FilamentProfile(
            id="bambu_asa",
            brand="Bambu Lab",
            material_name="ASA",
            category=MaterialCategory.ASA,
            density_g_cm3=1.06,
            nozzle_temp_min=240.0,
            nozzle_temp_max=270.0,
            nozzle_temp_recommended=260.0,
            bed_temp_min=90.0,
            bed_temp_max=110.0,
            bed_temp_recommended=100.0,
            max_volumetric_speed_mm3_s=14.0,
            cooling_fan_min_pct=10.0,
            cooling_fan_max_pct=30.0,
            enclosure_required=True,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="UV and weather-resistant outdoor ABS alternative; requires heated enclosure."
        ),

        # 9. Bambu Lab TPU 95A
        "bambu_tpu_95a": FilamentProfile(
            id="bambu_tpu_95a",
            brand="Bambu Lab",
            material_name="TPU 95A",
            category=MaterialCategory.TPU,
            density_g_cm3=1.22,
            nozzle_temp_min=200.0,
            nozzle_temp_max=240.0,
            nozzle_temp_recommended=225.0,
            bed_temp_min=30.0,
            bed_temp_max=50.0,
            bed_temp_recommended=35.0,
            max_volumetric_speed_mm3_s=3.2,
            outer_wall_speed_mm_s=25.0,
            inner_wall_speed_mm_s=35.0,
            sparse_infill_speed_mm_s=40.0,
            cooling_fan_min_pct=70.0,
            cooling_fan_max_pct=100.0,
            retraction_length_mm=0.6,
            retraction_speed_mm_s=20.0,
            enclosure_required=False,
            is_abrasive=False,
            moisture_sensitive=True,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Flexible elastomer. Slow speed and low volumetric flow (3.2mm³/s) essential to avoid extruder jamming."
        ),

        # 10. Bambu Lab PC
        "bambu_pc": FilamentProfile(
            id="bambu_pc",
            brand="Bambu Lab",
            material_name="Polycarbonate (PC)",
            category=MaterialCategory.PC,
            density_g_cm3=1.20,
            nozzle_temp_min=260.0,
            nozzle_temp_max=290.0,
            nozzle_temp_recommended=275.0,
            bed_temp_min=95.0,
            bed_temp_max=115.0,
            bed_temp_recommended=105.0,
            max_volumetric_speed_mm3_s=16.0,
            cooling_fan_min_pct=0.0,
            cooling_fan_max_pct=20.0,
            enclosure_required=True,
            is_abrasive=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Engineering optical thermoplastic with 110°C HDT. Extreme warp risk without enclosure."
        ),

        # 11. Bambu Lab PLA-CF
        "bambu_pla_cf": FilamentProfile(
            id="bambu_pla_cf",
            brand="Bambu Lab",
            material_name="PLA-CF",
            category=MaterialCategory.PLA_CF,
            density_g_cm3=1.26,
            nozzle_temp_min=210.0,
            nozzle_temp_max=240.0,
            nozzle_temp_recommended=225.0,
            bed_temp_min=45.0,
            bed_temp_max=65.0,
            bed_temp_recommended=55.0,
            max_volumetric_speed_mm3_s=18.0,
            is_abrasive=True,
            enclosure_required=False,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Carbon fiber reinforced PLA. ABRASIVE: Hardened steel nozzle required."
        ),

        # 12. Bambu Lab PA-CF
        "bambu_pa_cf": FilamentProfile(
            id="bambu_pa_cf",
            brand="Bambu Lab",
            material_name="PA-CF (Carbon Fiber Nylon)",
            category=MaterialCategory.PA_CF,
            density_g_cm3=1.18,
            nozzle_temp_min=280.0,
            nozzle_temp_max=300.0,
            nozzle_temp_recommended=290.0,
            bed_temp_min=80.0,
            bed_temp_max=100.0,
            bed_temp_recommended=90.0,
            max_volumetric_speed_mm3_s=14.0,
            cooling_fan_min_pct=0.0,
            cooling_fan_max_pct=40.0,
            drying_temp_c=80.0,
            drying_duration_hrs=12.0,
            is_abrasive=True,
            enclosure_required=True,
            moisture_sensitive=True,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="High strength engineering composite. Severe moisture uptake; MUST be dried prior to printing."
        ),

        # User Spool: PLA SILK+ Gold (Generic / 200-220°C calibrated for delicate facial figurines)
        "pla_silk_plus_gold": FilamentProfile(
            id="pla_silk_plus_gold",
            brand="Silk+",
            material_name="PLA SILK+ Gold",
            category=MaterialCategory.PLA_SILK,
            density_g_cm3=1.22,
            nozzle_temp_min=200.0,
            nozzle_temp_max=220.0,
            nozzle_temp_recommended=208.0,
            bed_temp_min=45.0,
            bed_temp_max=65.0,
            bed_temp_recommended=55.0,
            max_volumetric_speed_mm3_s=11.0,
            outer_wall_speed_mm_s=40.0,
            inner_wall_speed_mm_s=80.0,
            sparse_infill_speed_mm_s=120.0,
            cooling_fan_min_pct=90.0,
            cooling_fan_max_pct=100.0,
            fan_off_first_layers=1,
            flow_ratio=0.97,
            retraction_length_mm=0.8,
            retraction_speed_mm_s=30.0,
            drying_temp_c=45.0,
            drying_duration_hrs=6.0,
            enclosure_required=False,
            is_abrasive=False,
            moisture_sensitive=True,
            provenance=ProfileProvenance.MANUFACTURER_VERIFIED,
            notes="Calibrated for user's 200-220°C Gold Silk spool. 208°C anti-sag, 40mm/s wall speed for pure metallic luster, and 0.26mm non-stick support Z-gap."
        ),
    }

    @classmethod
    def get_profile(cls, name_or_id: str = "pla_basic", brand: Optional[str] = None) -> FilamentProfile:
        """
        Retrieves matching filament profile. Safe fallback to Bambu PLA Basic if unrecognized.
        """
        clean_key = name_or_id.lower().replace(" ", "_").replace("-", "_")

        # Direct key match
        if clean_key in cls._REGISTRY:
            return cls._REGISTRY[clean_key]

        # Brand prefix match (e.g. "bambu_pla_basic")
        if brand:
            brand_key = f"{brand.lower().replace(' ', '_')}_{clean_key}"
            if brand_key in cls._REGISTRY:
                return cls._REGISTRY[brand_key]

        # Search by category or material name
        for p in cls._REGISTRY.values():
            if clean_key in p.category.value or clean_key in p.id:
                return p

        # Default fallback
        return cls._REGISTRY["bambu_pla_basic"]

    @classmethod
    def register_profile(cls, profile: FilamentProfile, overwrite: bool = False) -> None:
        """Registers a custom or user-calibrated filament profile."""
        key = profile.id.lower().replace(" ", "_").replace("-", "_")
        if key in cls._REGISTRY and not overwrite:
            raise ValueError(f"Filament profile '{profile.id}' already exists. Pass overwrite=True to update.")
        cls._REGISTRY[key] = profile

    @classmethod
    def list_filaments(cls) -> List[FilamentProfile]:
        """Returns all registered filament profiles."""
        return list(cls._REGISTRY.values())

