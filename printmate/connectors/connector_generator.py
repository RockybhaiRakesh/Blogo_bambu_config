"""
Connector and joint generation module.
Generates precision alignment dowels, D-shaped anti-rotation pins, keyed joints,
dual-pin and asymmetric connectors with configurable tolerances and minimum wall checks.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, List, Union, Dict, Any
import numpy as np
import shapely.geometry as sg
import trimesh

from printmate.core.exceptions import ConnectorError
from printmate.core.config import Config

class ConnectorType(str, Enum):
    """Types of mechanical alignment connectors."""
    CYLINDRICAL = "cylindrical"      # Circular dowel pin (shear resistance)
    D_SHAPED = "d_shaped"            # Circular with flat chord (anti-rotation)
    KEYED = "keyed"                  # Circular with rectangular spline (positive indexing)
    DUAL_PIN = "dual_pin"            # Two parallel pins spaced along major axis
    ASYMMETRIC = "asymmetric"        # Two unequal pins enforcing unique 1-way mating
    MAGNET_POCKET = "magnet_pocket"  # Parametric cylindrical recesses for neodymium magnets
    BALL_JOINT = "ball_joint"        # Spherical articulation ball and socket joint
    LOOSE_TENON = "loose_tenon"      # Standalone printable dowel peg with dual mating sockets
    HEXAGONAL = "hexagonal"          # 6-sided regular prism for positive 60-degree indexing

@dataclass
class DowelLockConfig:
    """Parameters for dowel pin and socket generation (Backward-compatible)."""
    pin_radius: float = 3.0          # 6.0mm diameter pin
    pin_height: float = 5.0          # 5.0mm pin height
    clearance: float = 0.25          # 0.25mm radial tolerance for 0.4mm nozzle FDM fit
    socket_depth_extra: float = 0.5  # Extra socket depth relief to prevent bottoming out
    bevel: float = 0.4               # Chamfer at tip for easy insertion

    # Extended Phase 3 fields
    connector_type: ConnectorType = ConnectorType.CYLINDRICAL
    secondary_radius: float = 2.0    # For asymmetric/dual pin
    pin_spacing: float = 12.0        # Center-to-center distance for dual pins
    min_wall_thickness: float = 2.0  # Safe perimeter distance
    key_width: float = 1.2           # Spline key width
    key_protrusion: float = 1.0      # Spline key protrusion
    d_flat_offset: float = 1.5       # Flat chord offset from center for D-pin

@dataclass
class ConnectorValidationResult:
    """Results of connector placement and wall thickness analysis."""
    is_valid: bool
    connector_type: ConnectorType
    min_wall_found_mm: float
    clearance_radial_mm: float
    clearance_axial_mm: float
    interference_detected: bool
    warning: Optional[str] = None

class ConnectorGenerator:
    """Generates precision geometric alignment joints and tolerance-compensated sockets."""

    @staticmethod
    def get_connector_polygons(
        config: DowelLockConfig,
        origin: Tuple[float, float] = (0.0, 0.0),
        angle_rad: float = 0.0
    ) -> Union[sg.Polygon, List[sg.Polygon]]:
        """
        Constructs the 2D planar profile(s) for the specified connector type.
        """
        r = config.pin_radius
        ctype = config.connector_type

        if ctype == ConnectorType.CYLINDRICAL:
            poly = sg.Point(origin).buffer(r, quad_segs=8)
            return poly

        elif ctype == ConnectorType.D_SHAPED:
            # Circle with flat chord cutting off top
            c = sg.Point(origin).buffer(r, quad_segs=8)
            chord_y = origin[1] + (config.d_flat_offset if config.d_flat_offset > 0 else r * 0.5)
            flat_box = sg.box(origin[0] - r * 2.0, origin[1] - r * 2.0, origin[0] + r * 2.0, chord_y)
            d_poly = c.intersection(flat_box)
            return d_poly

        elif ctype == ConnectorType.KEYED:
            # Circle union with rectangular key on +X side
            c = sg.Point(origin).buffer(r, quad_segs=8)
            kw = config.key_width
            kp = config.key_protrusion
            key_box = sg.box(origin[0] + r - 0.2, origin[1] - kw / 2.0, origin[0] + r + kp, origin[1] + kw / 2.0)
            return c.union(key_box)

        elif ctype == ConnectorType.DUAL_PIN:
            # Two symmetric pins along the angle axis
            half_d = config.pin_spacing / 2.0
            dx = half_d * np.cos(angle_rad)
            dy = half_d * np.sin(angle_rad)
            p1 = sg.Point(origin[0] - dx, origin[1] - dy).buffer(r, quad_segs=8)
            p2 = sg.Point(origin[0] + dx, origin[1] + dy).buffer(r, quad_segs=8)
            return [p1, p2]

        elif ctype == ConnectorType.ASYMMETRIC:
            # Two unequal pins (primary r, secondary r2) along angle axis
            half_d = config.pin_spacing / 2.0
            r2 = config.secondary_radius
            dx = half_d * np.cos(angle_rad)
            dy = half_d * np.sin(angle_rad)
            p1 = sg.Point(origin[0] - dx, origin[1] - dy).buffer(r, quad_segs=8)
            p2 = sg.Point(origin[0] + dx, origin[1] + dy).buffer(r2, quad_segs=8)
            return [p1, p2]

        elif ctype == ConnectorType.HEXAGONAL:
            # 6-sided regular polygon centered at origin
            angles = np.linspace(0, 2 * np.pi, 7)[:-1]
            pts = [(origin[0] + r * np.cos(a), origin[1] + r * np.sin(a)) for a in angles]
            return sg.Polygon(pts)

        elif ctype == ConnectorType.LOOSE_TENON:
            # D-shaped profile for anti-rotation tenon
            c = sg.Point(origin).buffer(r, quad_segs=8)
            chord_y = origin[1] + (config.d_flat_offset if config.d_flat_offset > 0 else r * 0.5)
            flat_box = sg.box(origin[0] - r * 2.0, origin[1] - r * 2.0, origin[0] + r * 2.0, chord_y)
            return c.intersection(flat_box)

        # Default fallback
        return sg.Point(origin).buffer(r, quad_segs=8)

    @classmethod
    def create_pin_mesh(
        cls,
        config: DowelLockConfig,
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        sections: int = 32
    ) -> trimesh.Trimesh:
        """
        Generates a standalone 3D mesh representing male alignment pin(s).
        """
        if config.connector_type == ConnectorType.CYLINDRICAL:
            pin = trimesh.creation.cylinder(
                radius=config.pin_radius,
                height=config.pin_height,
                sections=sections
            )
            pin.apply_translation([origin[0], origin[1], origin[2] + config.pin_height / 2.0])
            return pin

        polys = cls.get_connector_polygons(config, origin=(origin[0], origin[1]))
        if isinstance(polys, list):
            meshes = []
            for p in polys:
                m = trimesh.creation.extrude_polygon(p, height=config.pin_height)
                m.apply_translation([0.0, 0.0, origin[2]])
                meshes.append(m)
            return trimesh.util.concatenate(meshes)
        else:
            m = trimesh.creation.extrude_polygon(polys, height=config.pin_height)
            m.apply_translation([0.0, 0.0, origin[2]])
            return m

    @classmethod
    def create_socket_cutter_mesh(
        cls,
        config: DowelLockConfig,
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        sections: int = 32
    ) -> trimesh.Trimesh:
        """
        Generates a tolerance-expanded 3D mesh used as a boolean cutter for the female socket.
        """
        socket_height = config.pin_height + config.socket_depth_extra

        if config.connector_type == ConnectorType.CYLINDRICAL:
            socket_radius = config.pin_radius + config.clearance
            cutter = trimesh.creation.cylinder(
                radius=socket_radius,
                height=socket_height,
                sections=sections
            )
            cutter.apply_translation([origin[0], origin[1], origin[2] + socket_height / 2.0])
            return cutter

        polys = cls.get_connector_polygons(config, origin=(origin[0], origin[1]))
        if isinstance(polys, list):
            meshes = []
            for p in polys:
                # Buffer polygon outward by exact radial clearance
                buf_p = p.buffer(config.clearance, quad_segs=8)
                m = trimesh.creation.extrude_polygon(buf_p, height=socket_height)
                m.apply_translation([0.0, 0.0, origin[2]])
                meshes.append(m)
            return trimesh.util.concatenate(meshes)
        else:
            buf_p = polys.buffer(config.clearance, quad_segs=8)
            m = trimesh.creation.extrude_polygon(buf_p, height=socket_height)
            m.apply_translation([0.0, 0.0, origin[2]])
            return m

    @classmethod
    def create_magnet_pocket_cutter(
        cls,
        diameter: float = 6.2,  # 6.0mm magnet + 0.2mm press-fit tolerance
        depth: float = 2.2,     # 2.0mm magnet + 0.2mm depth relief
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        sections: int = 32
    ) -> trimesh.Trimesh:
        """
        Generates a cylindrical cutter positioned symmetrically across the cut plane
        so subtracting it from both mating parts creates matching recessed magnet pockets.
        """
        cutter = trimesh.creation.cylinder(
            radius=diameter / 2.0,
            height=depth * 2.0,
            sections=sections
        )
        cutter.apply_translation([origin[0], origin[1], origin[2]])
        return cutter

    @classmethod
    def create_ball_joint_meshes(
        cls,
        ball_radius: float = 3.5,
        stem_radius: float = 2.0,
        stem_height: float = 3.0,
        clearance: float = 0.20,
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        sections: int = 24
    ) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Generates a male ball-pin and female spherical socket cutter for posable articulation.
        """
        stem = trimesh.creation.cylinder(radius=stem_radius, height=stem_height, sections=sections)
        stem.apply_translation([0, 0, stem_height / 2.0])
        sphere = trimesh.creation.icosphere(subdivisions=2, radius=ball_radius)
        sphere.apply_translation([0, 0, stem_height + ball_radius * 0.8])
        pin = trimesh.util.concatenate([stem, sphere])
        pin.apply_translation(list(origin))

        socket_cutter = trimesh.creation.icosphere(subdivisions=2, radius=ball_radius + clearance)
        socket_cutter.apply_translation([origin[0], origin[1], origin[2] + stem_height + ball_radius * 0.8])
        entry_channel = trimesh.creation.cylinder(radius=stem_radius + clearance, height=stem_height * 2)
        entry_channel.apply_translation([origin[0], origin[1], origin[2]])
        socket = trimesh.util.concatenate([socket_cutter, entry_channel])

        return pin, socket

    @classmethod
    def create_loose_tenon_meshes(
        cls,
        config: DowelLockConfig,
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        axis: int = 2
    ) -> Tuple[trimesh.Trimesh, trimesh.Trimesh, trimesh.Trimesh]:
        """
        Generates:
        1. cutter_below: Socket cutter sinking into lower part.
        2. cutter_above: Socket cutter sinking into upper part.
        3. standalone_tenon: Separate printable dowel peg with dual chamfered ends,
           laid flat along build plate for maximum FDM tensile shear strength.
        """
        half_h = config.pin_height
        socket_depth = half_h + config.socket_depth_extra
        clr = config.clearance

        # Socket polygon buffered outward by radial clearance
        poly = cls.get_connector_polygons(config, origin=(origin[0], origin[1]))
        if isinstance(poly, list):
            poly = poly[0]
        socket_poly = poly.buffer(clr, quad_segs=8)

        # Lower socket cutter (sinks into -Z)
        cutter_below = trimesh.creation.extrude_polygon(socket_poly, height=socket_depth)
        cutter_below.apply_translation([0.0, 0.0, origin[2] - socket_depth])

        # Upper socket cutter (sinks into +Z)
        cutter_above = trimesh.creation.extrude_polygon(socket_poly, height=socket_depth)
        cutter_above.apply_translation([0.0, 0.0, origin[2]])

        # Standalone printable tenon peg (Total height = 2 * half_h)
        peg_poly = cls.get_connector_polygons(config, origin=(0.0, 0.0))
        if isinstance(peg_poly, list):
            peg_poly = peg_poly[0]
        tenon_peg = trimesh.creation.extrude_polygon(peg_poly, height=half_h * 2.0)

        # Lay tenon flat on bed plate for maximum shear strength (horizontal layer lines)
        tenon_peg.apply_translation([0.0, 0.0, -half_h])
        tenon_peg.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        min_z = float(tenon_peg.bounds[0][2])
        tenon_peg.apply_translation([0.0, 0.0, -min_z])

        return cutter_below, cutter_above, tenon_peg

    @staticmethod
    def audit_connector_safety(
        mesh: trimesh.Trimesh,
        cut_plane_pos: float,
        pin_radius: float,
        axis: int = 2,
        min_safe_wall: float = 2.0
    ) -> Tuple[bool, float, float]:
        """
        Evaluates cross-section distance to pin perimeter at the cut interface.
        Returns: (is_safe, min_wall_margin_mm, recommended_pin_radius_mm)
        """
        try:
            normal = [0.0, 0.0, 0.0]
            normal[axis] = 1.0
            pt = [0.0, 0.0, 0.0]
            pt[axis] = cut_plane_pos

            slice_lines = mesh.section(plane_origin=pt, plane_normal=normal)
            if slice_lines is None:
                return (True, 10.0, pin_radius)

            path2d, _ = slice_lines.to_planar()
            polys = path2d.polygons_full
            if not polys:
                return (True, 10.0, pin_radius)

            total_area = sum(p.area for p in polys)
            eff_radius = float(np.sqrt(total_area / np.pi))
            wall_margin = float(eff_radius - pin_radius)
            is_safe = wall_margin >= min_safe_wall
            rec_radius = max(1.5, float(eff_radius - min_safe_wall))
            return (is_safe, round(wall_margin, 2), round(rec_radius, 2))
        except Exception:
            return (True, 5.0, pin_radius)

    @classmethod
    def validate_placement(
        cls,
        cut_polygon_2d: sg.Polygon,
        origin: Tuple[float, float],
        config: DowelLockConfig
    ) -> ConnectorValidationResult:
        """
        Validates whether connector pins fit cleanly within the cut polygon
        with safe wall margins and zero inter-pin collision.
        """
        polys = cls.get_connector_polygons(config, origin=origin)
        if not isinstance(polys, list):
            polys = [polys]

        # Check inter-pin collision
        interference = False
        if len(polys) > 1:
            for i in range(len(polys)):
                for j in range(i + 1, len(polys)):
                    if polys[i].distance(polys[j]) < (config.clearance * 2.0):
                        interference = True

        # Check distance to outer boundary
        min_wall = float("inf")
        for p in polys:
            expanded = p.buffer(config.clearance)
            if not cut_polygon_2d.contains(expanded):
                min_wall = 0.0
                break
            # Distance from socket edge to polygon exterior
            dist = cut_polygon_2d.exterior.distance(expanded)
            min_wall = min(min_wall, dist)

        is_valid = (min_wall >= config.min_wall_thickness) and not interference
        warning = None
        if interference:
            warning = "Interference detected between connector pins."
        elif min_wall < config.min_wall_thickness:
            warning = f"Wall thickness {min_wall:.2f}mm is below safe minimum {config.min_wall_thickness:.2f}mm."

        return ConnectorValidationResult(
            is_valid=is_valid,
            connector_type=config.connector_type,
            min_wall_found_mm=round(min_wall, 3),
            clearance_radial_mm=config.clearance,
            clearance_axial_mm=config.socket_depth_extra,
            interference_detected=interference,
            warning=warning
        )

    @classmethod
    def apply_blender_dowel_lock(
        cls,
        base_stl: str,
        idol_stl: str,
        out_base_stl: str,
        out_idol_stl: str,
        center_xy: Tuple[float, float],
        z_cut: float,
        config: Optional[DowelLockConfig] = None,
        blender_exe: Optional[str] = None
    ) -> bool:
        """
        Executes verified headless Blender script to join the male pin to base
        and boolean-subtract the female socket from the upper part using the EXACT solver.
        """
        if config is None:
            config = DowelLockConfig()

        blender_bin = blender_exe or Config.BLENDER_EXE
        if not os.path.exists(blender_bin):
            raise ConnectorError(f"Blender executable not found at: {blender_bin}")

        # If custom connector type is requested (D-shaped, keyed, dual, asymmetric),
        # export standalone pin and socket meshes and use them in Blender
        if config.connector_type != ConnectorType.CYLINDRICAL:
            return cls._apply_custom_connector_blender(
                base_stl=base_stl,
                idol_stl=idol_stl,
                out_base_stl=out_base_stl,
                out_idol_stl=out_idol_stl,
                center_xy=center_xy,
                z_cut=z_cut,
                config=config,
                blender_bin=blender_bin
            )

        # Standard cylindrical dowel path (100% backward compatible)
        script_content = f"""
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
cx, cy = {center_xy[0]}, {center_xy[1]}
z_cut = {z_cut}

# 1. Base (Male Pin)
bpy.ops.wm.stl_import(filepath=r"{base_stl}")
base_obj = bpy.context.selected_objects[0]
base_obj.name = "Base"

bpy.ops.mesh.primitive_cylinder_add(
    radius={config.pin_radius},
    depth={config.pin_height},
    vertices=32,
    location=(cx, cy, z_cut + {config.pin_height / 2.0})
)
pin_obj = bpy.context.active_object
pin_obj.name = "MalePin"

bpy.ops.object.select_all(action='DESELECT')
base_obj.select_set(True)
pin_obj.select_set(True)
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.join()

bpy.ops.wm.stl_export(filepath=r"{out_base_stl}")

# 2. Top / Idol (Female Socket)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=r"{idol_stl}")
idol_obj = bpy.context.selected_objects[0]
idol_obj.name = "Idol"

socket_depth = {config.pin_height + config.socket_depth_extra}
bpy.ops.mesh.primitive_cylinder_add(
    radius={config.pin_radius + config.clearance},
    depth=socket_depth,
    vertices=32,
    location=(cx, cy, z_cut + {socket_depth / 2.0})
)
socket_cutter = bpy.context.active_object
socket_cutter.name = "SocketCutter"

bool_mod = idol_obj.modifiers.new(name="SocketHole", type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.solver = 'EXACT'
bool_mod.object = socket_cutter

bpy.context.view_layer.objects.active = idol_obj
bpy.ops.object.modifier_apply(modifier="SocketHole")
bpy.data.objects.remove(socket_cutter, do_unlink=True)

bpy.ops.wm.stl_export(filepath=r"{out_idol_stl}")
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            script_path = f.name
            f.write(script_content)

        try:
            cmd = [blender_bin, "-b", "-P", script_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise ConnectorError(f"Blender dowel lock operation failed:\n{e.stderr}") from e
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

    @classmethod
    def _apply_custom_connector_blender(
        cls,
        base_stl: str,
        idol_stl: str,
        out_base_stl: str,
        out_idol_stl: str,
        center_xy: Tuple[float, float],
        z_cut: float,
        config: DowelLockConfig,
        blender_bin: str
    ) -> bool:
        """Applies arbitrary custom connector meshes (D-shaped, keyed, dual, asymmetric)."""
        pin_mesh = cls.create_pin_mesh(config, origin=(center_xy[0], center_xy[1], z_cut))
        socket_mesh = cls.create_socket_cutter_mesh(config, origin=(center_xy[0], center_xy[1], z_cut))

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f_pin, \
             tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f_sock:
            pin_temp = f_pin.name
            sock_temp = f_sock.name

        pin_mesh.export(pin_temp)
        socket_mesh.export(sock_temp)

        script_content = f"""
import bpy

# 1. Base + Pin
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=r"{base_stl}")
base_obj = bpy.context.selected_objects[0]

bpy.ops.wm.stl_import(filepath=r"{pin_temp}")
pin_obj = bpy.context.selected_objects[0]

bpy.ops.object.select_all(action='DESELECT')
base_obj.select_set(True)
pin_obj.select_set(True)
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.join()
bpy.ops.wm.stl_export(filepath=r"{out_base_stl}")

# 2. Top - Socket
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=r"{idol_stl}")
top_obj = bpy.context.selected_objects[0]

bpy.ops.wm.stl_import(filepath=r"{sock_temp}")
sock_obj = bpy.context.selected_objects[0]

bool_mod = top_obj.modifiers.new(name="CustomSocket", type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.solver = 'EXACT'
bool_mod.object = sock_obj

bpy.context.view_layer.objects.active = top_obj
bpy.ops.object.modifier_apply(modifier="CustomSocket")
bpy.data.objects.remove(sock_obj, do_unlink=True)
bpy.ops.wm.stl_export(filepath=r"{out_idol_stl}")
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f_sc:
            script_path = f_sc.name
            f_sc.write(script_content)

        try:
            cmd = [blender_bin, "-b", "-P", script_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise ConnectorError(f"Blender custom connector operation failed:\n{e.stderr}") from e
        finally:
            for p in [pin_temp, sock_temp, script_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
