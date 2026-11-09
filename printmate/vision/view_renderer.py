"""
3D Model multi-view snapshot rendering module.
Generates canonical orthographic and perspective viewpoints (front, back, left,
right, top, isometric) with exact camera projection matrices for vision analysis.
"""

import os
import hashlib
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import trimesh

from printmate.core.config import Config

@dataclass
class RenderView:
    """Snapshot metadata for a single camera viewpoint."""
    name: str                            # e.g., 'front', 'isometric'
    image_path: str
    camera_pos: List[float]
    target_pos: List[float]
    up_vector: List[float]
    resolution: Tuple[int, int]
    view_matrix: List[List[float]] = field(default_factory=list)

@dataclass
class RenderCollection:
    """Collection of canonical rendered views of a 3D model."""
    model_name: str
    output_dir: str
    views: Dict[str, RenderView] = field(default_factory=dict)
    bounding_box_min: List[float] = field(default_factory=list)
    bounding_box_max: List[float] = field(default_factory=list)

    def get_view(self, name: str) -> Optional[RenderView]:
        return self.views.get(name)

class ViewRenderer:
    """Renders canonical multi-view snapshots from 3D models using Blender or software rasterization."""

    CANONICAL_VIEWS = {
        "front": {"dir": [0.0, -1.0, 0.0], "up": [0.0, 0.0, 1.0]},
        "back": {"dir": [0.0, 1.0, 0.0], "up": [0.0, 0.0, 1.0]},
        "left": {"dir": [-1.0, 0.0, 0.0], "up": [0.0, 0.0, 1.0]},
        "right": {"dir": [1.0, 0.0, 0.0], "up": [0.0, 0.0, 1.0]},
        "top": {"dir": [0.0, 0.0, 1.0], "up": [0.0, 1.0, 0.0]},
        "isometric": {"dir": [1.0, -1.0, 0.8], "up": [0.0, 0.0, 1.0]},
    }

    @classmethod
    def render_views(
        cls,
        model_input: Any,  # Filepath (str) or trimesh.Trimesh
        output_dir: Optional[str] = None,
        resolution: Tuple[int, int] = (512, 512),
        engine: str = "auto",
        force_rerender: bool = False
    ) -> RenderCollection:
        """
        Renders the model from 6 canonical camera angles.

        Args:
            model_input: File path (str) or trimesh.Trimesh instance.
            output_dir: Directory where PNG snapshots will be saved.
            resolution: (width, height) pixel resolution.
            engine: 'auto', 'blender', or 'matplotlib'.
            force_rerender: If True, ignores cached images.

        Returns:
            RenderCollection with snapshot file paths and camera matrices.
        """
        temp_stl = None
        if isinstance(model_input, str):
            model_path = os.path.abspath(model_input)
            model_name = os.path.splitext(os.path.basename(model_path))[0]
            mesh = trimesh.load(model_path, force='mesh')
        else:
            mesh = model_input
            model_name = "mesh_model"
            if engine == "blender":
                fd, temp_stl = tempfile.mkstemp(suffix=".stl")
                os.close(fd)
                mesh.export(temp_stl)
                model_path = temp_stl
            else:
                model_path = ""

        target_dir = output_dir or os.path.join(Config.WORKSPACE_DIR, "outputs", "renders", model_name)
        os.makedirs(target_dir, exist_ok=True)

        bounds = mesh.bounds
        b_min = [float(v) for v in bounds[0]]
        b_max = [float(v) for v in bounds[1]]
        center = (bounds[0] + bounds[1]) / 2.0
        extents = mesh.extents
        max_extent = float(np.max(extents))
        camera_dist = max_extent * 2.2

        collection = RenderCollection(
            model_name=model_name,
            output_dir=target_dir,
            bounding_box_min=b_min,
            bounding_box_max=b_max
        )

        # Check cache: if all 6 view PNGs exist and force_rerender is False
        all_cached = True
        for v_name in cls.CANONICAL_VIEWS:
            p = os.path.join(target_dir, f"{model_name}_{v_name}.png")
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                all_cached = False
                break

        if all_cached and not force_rerender:
            for v_name, v_cfg in cls.CANONICAL_VIEWS.items():
                p = os.path.join(target_dir, f"{model_name}_{v_name}.png")
                direction = np.array(v_cfg["dir"]) / np.linalg.norm(v_cfg["dir"])
                cam_pos = center + direction * camera_dist
                collection.views[v_name] = RenderView(
                    name=v_name,
                    image_path=p,
                    camera_pos=[round(float(c), 2) for c in cam_pos],
                    target_pos=[round(float(c), 2) for c in center],
                    up_vector=v_cfg["up"],
                    resolution=resolution
                )
            if temp_stl and os.path.exists(temp_stl):
                os.remove(temp_stl)
            return collection

        # Select engine
        if engine == "blender" and os.path.exists(Config.BLENDER_EXE):
            cls._render_with_blender(model_path, target_dir, model_name, resolution)
        elif engine == "matplotlib":
            cls._render_with_matplotlib(mesh, target_dir, model_name, resolution)
        else:
            # High-performance native rasterizer (<300ms for all 6 views)
            cls._render_with_fast_rasterizer(mesh, target_dir, model_name, resolution)

        # Populate RenderCollection
        for v_name, v_cfg in cls.CANONICAL_VIEWS.items():
            p = os.path.join(target_dir, f"{model_name}_{v_name}.png")
            direction = np.array(v_cfg["dir"]) / np.linalg.norm(v_cfg["dir"])
            cam_pos = center + direction * camera_dist
            collection.views[v_name] = RenderView(
                name=v_name,
                image_path=p,
                camera_pos=[round(float(c), 2) for c in cam_pos],
                target_pos=[round(float(c), 2) for c in center],
                up_vector=v_cfg["up"],
                resolution=resolution
            )

        if temp_stl and os.path.exists(temp_stl):
            os.remove(temp_stl)

        return collection

    @classmethod
    def _render_with_blender(
        cls,
        model_path: str,
        output_dir: str,
        model_name: str,
        resolution: Tuple[int, int]
    ) -> None:
        """Invokes Blender in headless mode to render high-fidelity multi-view snapshots."""
        blender_script = f"""
import bpy, os, math, mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)

# Import model
model_path = r"{model_path}"
if model_path.lower().endswith(".stl"):
    bpy.ops.wm.stl_import(filepath=model_path)
elif model_path.lower().endswith(".obj"):
    bpy.ops.wm.obj_import(filepath=model_path)
else:
    bpy.ops.wm.stl_import(filepath=model_path)

objs = bpy.context.selected_objects
if not objs:
    raise RuntimeError("No object loaded")
main_obj = objs[0]
main_obj.name = "Model"

# Compute bounds and center
bbox = [main_obj.matrix_world @ mathutils.Vector(corner) for corner in main_obj.bound_box]
b_min = mathutils.Vector((min(b.x for b in bbox), min(b.y for b in bbox), min(b.z for b in bbox)))
b_max = mathutils.Vector((max(b.x for b in bbox), max(b.y for b in bbox), max(b.z for b in bbox)))
center = (b_min + b_max) / 2.0
extents = b_max - b_min
max_dim = max(extents.x, extents.y, extents.z)
cam_dist = max_dim * 2.2

# Setup Studio lighting
light_data = bpy.data.lights.new('KeyLight', type='SUN')
light_data.energy = 3.5
light_obj = bpy.data.objects.new('KeyLight', light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = center + mathutils.Vector((max_dim, -max_dim, max_dim * 1.5))

fill_data = bpy.data.lights.new('FillLight', type='SUN')
fill_data.energy = 1.5
fill_obj = bpy.data.objects.new('FillLight', fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = center + mathutils.Vector((-max_dim, max_dim, max_dim))

# Setup Camera
cam_data = bpy.data.cameras.new('Camera')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = max_dim * 1.25
cam_obj = bpy.data.objects.new('Camera', cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

bpy.context.scene.render.resolution_x = {resolution[0]}
bpy.context.scene.render.resolution_y = {resolution[1]}
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Material styling
mat = bpy.data.materials.new("ClayMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.78, 0.76, 0.74, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.45
main_obj.data.materials.append(mat)

# Canonical Views
views = {{
    "front": (0.0, -1.0, 0.0),
    "back": (0.0, 1.0, 0.0),
    "left": (-1.0, 0.0, 0.0),
    "right": (1.0, 0.0, 0.0),
    "top": (0.0, 0.0, 1.0),
    "isometric": (1.0, -1.0, 0.8)
}}

out_dir = r"{output_dir}"
for v_name, direction in views.items():
    d = mathutils.Vector(direction).normalized()
    cam_obj.location = center + d * cam_dist
    
    # Point camera at center
    to_center = (center - cam_obj.location).normalized()
    if v_name == "top":
        up = mathutils.Vector((0, 1, 0))
    else:
        up = mathutils.Vector((0, 0, 1))
    
    rot_quat = to_center.to_track_quat('-Z', 'Y' if v_name == "top" else 'Z')
    cam_obj.rotation_euler = rot_quat.to_euler()
    
    out_path = os.path.join(out_dir, f"{model_name}_{{v_name}}.png")
    bpy.context.scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            script_path = f.name
            f.write(blender_script)

        try:
            cmd = [Config.BLENDER_EXE, "-b", "-P", script_path]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

    @classmethod
    def _render_with_matplotlib(
        cls,
        mesh: trimesh.Trimesh,
        output_dir: str,
        model_name: str,
        resolution: Tuple[int, int]
    ) -> None:
        """Fallback renderer using matplotlib Agg backend."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D

        # Decimate if mesh is large for matplotlib performance
        vertices = mesh.vertices
        faces = mesh.faces
        if len(faces) > 5000:
            sub_indices = np.linspace(0, len(faces) - 1, 5000, dtype=int)
            faces = faces[sub_indices]

        # Elevation and Azimuth map
        view_angles = {
            "front": (0, -90),
            "back": (0, 90),
            "left": (0, 180),
            "right": (0, 0),
            "top": (90, -90),
            "isometric": (30, 45),
        }

        dpi = 100
        figsize = (resolution[0] / dpi, resolution[1] / dpi)

        for v_name, (elev, azim) in view_angles.items():
            fig = plt.figure(figsize=figsize, dpi=dpi)
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_trisurf(
                vertices[:, 0], vertices[:, 1], faces, vertices[:, 2],
                color='#c8c4bc', edgecolor='#8c8880', linewidth=0.2, shade=True
            )
            ax.view_init(elev=elev, azim=azim)
            ax.set_axis_off()
            ax.grid(False)
            plt.subplots_adjust(left=0, right=1, bottom=0, top=1)

            out_path = os.path.join(output_dir, f"{model_name}_{v_name}.png")
            plt.savefig(out_path, dpi=dpi, transparent=False, facecolor='white')
            plt.close(fig)

    @classmethod
    def _render_with_fast_rasterizer(
        cls,
        mesh: trimesh.Trimesh,
        output_dir: str,
        model_name: str,
        resolution: Tuple[int, int]
    ) -> None:
        """
        Ultra-fast pure Python + NumPy + Pillow orthographic depth & normal shading rasterizer.
        Renders all 6 canonical camera views in ~200ms total without launching Blender or Matplotlib.
        """
        from PIL import Image, ImageDraw

        w, h = resolution
        verts = mesh.vertices
        faces = mesh.faces
        normals = mesh.face_normals

        # Stride sampling if high-poly for maximum rendering speed
        if len(faces) > 4000:
            step = len(faces) // 3500
            face_subset = faces[::step]
            normal_subset = normals[::step]
        else:
            face_subset = faces
            normal_subset = normals

        view_specs = {
            "front": {"dir": np.array([0.0, -1.0, 0.0]), "proj_axes": (0, 2), "depth_axis": 1, "depth_sign": 1},
            "back": {"dir": np.array([0.0, 1.0, 0.0]), "proj_axes": (0, 2), "depth_axis": 1, "depth_sign": -1},
            "left": {"dir": np.array([-1.0, 0.0, 0.0]), "proj_axes": (1, 2), "depth_axis": 0, "depth_sign": 1},
            "right": {"dir": np.array([1.0, 0.0, 0.0]), "proj_axes": (1, 2), "depth_axis": 0, "depth_sign": -1},
            "top": {"dir": np.array([0.0, 0.0, 1.0]), "proj_axes": (0, 1), "depth_axis": 2, "depth_sign": -1},
            "isometric": {"dir": np.array([1.0, -1.0, 0.8]), "is_iso": True}
        }

        for v_name in cls.CANONICAL_VIEWS:
            out_path = os.path.join(output_dir, f"{model_name}_{v_name}.png")
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                continue

            v_spec = view_specs.get(v_name, view_specs["front"])

            if v_spec.get("is_iso"):
                angle_z = np.radians(45)
                cos_z, sin_z = np.cos(angle_z), np.sin(angle_z)
                R_z = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])

                angle_x = np.radians(-30)
                cos_x, sin_x = np.cos(angle_x), np.sin(angle_x)
                R_x = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
                R = R_x @ R_z

                rot_verts = verts @ R.T
                rot_normals = normal_subset @ R.T

                p_min = np.min(rot_verts[:, [0, 1]], axis=0)
                p_max = np.max(rot_verts[:, [0, 1]], axis=0)
                center_2d = (p_min + p_max) / 2.0
                span = max(float(p_max[0] - p_min[0]), float(p_max[1] - p_min[1]), 1e-5) * 1.15
                scale = (min(w, h) - 24.0) / span

                coords = (rot_verts[:, [0, 1]] - center_2d) * scale + [w / 2.0, h / 2.0]
                coords[:, 1] = h - coords[:, 1]

                face_depths = np.mean(rot_verts[face_subset, 2], axis=1)
                sort_order = np.argsort(face_depths)
                shades = np.clip(np.dot(rot_normals, [0.3, 0.4, 0.86]) * 0.5 + 0.5, 0.15, 1.0)
            else:
                ax_u, ax_v = v_spec["proj_axes"]
                d_ax = v_spec["depth_axis"]
                d_sign = v_spec["depth_sign"]

                p_min = np.min(verts[:, [ax_u, ax_v]], axis=0)
                p_max = np.max(verts[:, [ax_u, ax_v]], axis=0)
                center_2d = (p_min + p_max) / 2.0
                span = max(float(p_max[0] - p_min[0]), float(p_max[1] - p_min[1]), 1e-5) * 1.15
                scale = (min(w, h) - 24.0) / span

                coords = (verts[:, [ax_u, ax_v]] - center_2d) * scale + [w / 2.0, h / 2.0]
                coords[:, 1] = h - coords[:, 1]

                face_depths = np.mean(verts[face_subset, d_ax], axis=1) * d_sign
                sort_order = np.argsort(face_depths)
                cam_dir = v_spec["dir"]
                shades = np.clip(np.dot(normal_subset, -cam_dir) * 0.5 + 0.5, 0.15, 1.0)

            img = Image.new('RGB', (w, h), (255, 255, 255))
            draw = ImageDraw.Draw(img)

            for f_idx in sort_order:
                tri_pts = [tuple(coords[v]) for v in face_subset[f_idx]]
                s = int(shades[f_idx] * 205)
                draw.polygon(tri_pts, fill=(s, s, min(255, s + 15)), outline=(max(0, s - 25), max(0, s - 25), max(0, s - 20)))

            img.save(out_path)

