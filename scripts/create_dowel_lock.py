import bpy
import bmesh
import math

import os

print("=== STARTING BLENDER DOWEL LOCK CREATION ===")

# Clear existing objects
bpy.ops.wm.read_factory_settings(use_empty=True)

cx = -3.16
cy = 1.56
z_cut = -23.5

# Detect models path
workspace = r"c:\Users\rakes\OneDrive\Desktop\3dMOdel_agent"
parts_dir = os.path.join(workspace, "models", "split_parts")
if not os.path.exists(parts_dir):
    parts_dir = workspace

# ---------------------------------------------------------
# 1. PROCESS BASE (MALE PIN)
# ---------------------------------------------------------
base_path = os.path.join(parts_dir, "Ayyappan_Part1_Base.stl")
print(f"Importing Base: {base_path}")
bpy.ops.wm.stl_import(filepath=base_path)
base_obj = bpy.context.selected_objects[0]
base_obj.name = "Base"

# Create Male Cylinder Pin: Diameter 6.0mm (radius 3.0mm), Height 5.0mm
# We place it at Z = z_cut + 2.5mm (so it extends from z_cut to z_cut + 5.0mm)
bpy.ops.mesh.primitive_cylinder_add(
    radius=3.0,
    depth=5.0,
    vertices=32,
    location=(cx, cy, z_cut + 2.5)
)
pin_obj = bpy.context.active_object
pin_obj.name = "MalePin"

# Add bevel to top of pin for smooth insertion
bpy.ops.object.select_all(action='DESELECT')
base_obj.select_set(True)
pin_obj.select_set(True)
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.join()

base_out_path = os.path.join(parts_dir, "Ayyappan_Part1_Base_MaleLock.stl")
print(f"Exporting Base with Male Pin: {base_out_path}")
bpy.ops.wm.stl_export(filepath=base_out_path)

# ---------------------------------------------------------
# 2. PROCESS IDOL (FEMALE SOCKET)
# ---------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)

idol_path = os.path.join(parts_dir, "Ayyappan_Part2_Idol.stl")
print(f"Importing Idol: {idol_path}")
bpy.ops.wm.stl_import(filepath=idol_path)
idol_obj = bpy.context.selected_objects[0]
idol_obj.name = "Idol"

# Create Female Socket Cylinder: Diameter 6.5mm (radius 3.25mm - 0.25mm clearance tolerance), Depth 5.5mm
# We place it from Z = z_cut - 0.5 to z_cut + 5.5 (depth 6mm, location Z = z_cut + 2.5)
bpy.ops.mesh.primitive_cylinder_add(
    radius=3.25,
    depth=6.0,
    vertices=32,
    location=(cx, cy, z_cut + 2.5)
)
socket_cutter = bpy.context.active_object
socket_cutter.name = "SocketCutter"

# Boolean Difference
print("Applying Boolean Difference for Female Socket...")
bool_mod = idol_obj.modifiers.new(name="SocketHole", type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.solver = 'EXACT'
bool_mod.object = socket_cutter

bpy.context.view_layer.objects.active = idol_obj
bpy.ops.object.modifier_apply(modifier="SocketHole")

# Delete cutter
bpy.data.objects.remove(socket_cutter, do_unlink=True)

idol_out_path = os.path.join(parts_dir, "Ayyappan_Part2_Idol_FemaleLock.stl")
print(f"Exporting Idol with Female Socket: {idol_out_path}")
bpy.ops.wm.stl_export(filepath=idol_out_path)

print("=== COMPLETED BLENDER DOWEL LOCK GENERATION ===")
