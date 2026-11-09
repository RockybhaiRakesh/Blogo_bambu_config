"""
Bambu Studio 3MF Project Generator module.
Packages 3D models into production-ready .3mf projects with injected configuration overrides.
"""

import os
import re
import json
import shutil
import zipfile
import tempfile
from typing import Dict, Any, Optional
from printmate.core.config import Config
from printmate.core.exceptions import SlicerIntegrationError
from printmate.optimization.strategy_optimizer import StrategyOptimizer
from printmate.slicer.slicer_validator import SlicerValidator

class BambuProjectGenerator:
    """Creates native Bambu Studio .3mf projects with verified slicer profiles."""

    @classmethod
    def generate(
        cls,
        input_file: str,
        output_3mf: str,
        mode: str = "single",
        filament: str = "pla_basic",
        target_height: Optional[float] = None,
        template_3mf: Optional[str] = None,
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Builds a native Bambu Studio .3mf project file with the user's actual 3D geometry
        and verified slicer process profiles.
        """
        if input_file and os.path.exists(input_file):
            return cls.generate_multi_part_project(
                parts=[input_file],
                output_3mf=output_3mf,
                filament=filament,
                mode=mode,
                target_height=target_height,
                custom_overrides=custom_overrides
            )

        template = template_3mf or Config.GOLDEN_TEMPLATE_3MF
        if not os.path.exists(template):
            raise SlicerIntegrationError(f"Golden template 3MF not found at: {template}")

        # Compute overrides from StrategyOptimizer
        config_overrides = StrategyOptimizer.build_slicer_overrides(
            mode=mode,
            filament=filament
        )
        if custom_overrides:
            config_overrides.update(custom_overrides)

        temp_dir = tempfile.mkdtemp(prefix="bambu_build_")
        try:
            # Extract golden template
            with zipfile.ZipFile(template, 'r') as z_in:
                z_in.extractall(temp_dir)

            # Read & patch project_settings.config
            cfg_path = os.path.join(temp_dir, "Metadata", "project_settings.config")
            if not os.path.exists(cfg_path):
                raise SlicerIntegrationError("Metadata/project_settings.config missing in template archive.")

            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)

            for k, v in config_overrides.items():
                cfg[k] = v

            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=4)

            # Update scale in model_settings.config if target_height is requested
            if target_height is not None:
                model_cfg_path = os.path.join(temp_dir, "Metadata", "model_settings.config")
                if os.path.exists(model_cfg_path):
                    with open(model_cfg_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Original reference template base height is 100.0mm
                    scale_val = round(float(target_height) / 100.0, 4)
                    z_center = round(float(target_height) / 2.0, 2)
                    content = re.sub(
                        r'transform="[0-9\.]+ 0 0 0 [0-9\.]+ 0 0 0 [0-9\.]+ 0 0 [0-9\.]+"',
                        f'transform="{scale_val} 0 0 0 {scale_val} 0 0 0 {scale_val} 0 0 {z_center}"',
                        content
                    )
                    with open(model_cfg_path, 'w', encoding='utf-8') as f:
                        f.write(content)

            # Ensure parent output directory exists
            out_dir = os.path.dirname(os.path.abspath(output_3mf))
            os.makedirs(out_dir, exist_ok=True)

            # Re-zip into output .3mf
            with zipfile.ZipFile(output_3mf, 'w', zipfile.ZIP_DEFLATED) as z_out:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, temp_dir)
                        z_out.write(full_p, rel_p)

            # Validate generated package
            valid, errs = SlicerValidator.validate_package(output_3mf)
            if not valid:
                raise SlicerIntegrationError(f"Generated 3MF failed validation: {'; '.join(errs)}")

            return os.path.abspath(output_3mf)

        except Exception as e:
            if isinstance(e, SlicerIntegrationError):
                raise
            raise SlicerIntegrationError(f"Failed to generate Bambu Studio project: {str(e)}") from e
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    @classmethod
    def generate_multi_part_project(
        cls,
        parts: list,
        output_3mf: str,
        filament: str = "pla_basic",
        mode: str = "split",
        target_height: Optional[float] = None,
        spacing_mm: float = 15.0,
        custom_overrides: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Creates a Bambu Studio .3mf project with real user mesh objects laid out on the build plate.

        Args:
            parts: List of filepaths or trimesh.Trimesh objects.
            output_3mf: Target path for the generated .3mf project.
            filament: Filament profile string.
            mode: "single" or "split".
            target_height: Optional uniform Z height scaling.
            spacing_mm: Spacing between parts on the build plate.
            custom_overrides: Custom slicer profile dictionary overrides.

        Returns:
            Absolute path to generated .3mf file.
        """
        import trimesh
        from printmate.geometry.loader import load_mesh
        meshes = []
        for p in parts:
            if isinstance(p, str):
                meshes.append(load_mesh(p))
            elif isinstance(p, trimesh.Trimesh):
                meshes.append(p.copy())

        if not meshes:
            raise SlicerIntegrationError("No valid meshes provided for project generation.")

        # Scale if target_height requested
        if target_height is not None and target_height > 0:
            for m in meshes:
                h = float(m.extents[2])
                if h > 0:
                    m.apply_scale(target_height / h)

        # Layout meshes along X axis with spacing
        current_x = 0.0
        arranged_meshes = []
        for m in meshes:
            # Place base of mesh on Z=0
            min_z = float(m.bounds[0][2])
            m.apply_translation([0, 0, -min_z])
            # Center on Y=0
            y_mid = float(m.bounds[0][1] + m.bounds[1][1]) / 2.0
            m.apply_translation([0, -y_mid, 0])
            # Shift along X
            min_x = float(m.bounds[0][0])
            m.apply_translation([current_x - min_x, 0, 0])
            arranged_meshes.append(m)
            current_x = float(m.bounds[1][0]) + spacing_mm

        # Center entire group on Bambu Lab A1 plate center (128.0, 128.0)
        total_width = current_x - spacing_mm
        shift_back = total_width / 2.0
        for m in arranged_meshes:
            m.apply_translation([128.0 - shift_back, 128.0, 0.0])

        scene = trimesh.Scene(arranged_meshes)

        # Generate base 3MF
        temp_dir = tempfile.mkdtemp(prefix="bambu_multi_")
        temp_raw_3mf = os.path.join(temp_dir, "raw_scene.3mf")
        try:
            scene.export(temp_raw_3mf, file_type='3mf')

            # 1. Base project settings and slicer metadata from Golden Template
            golden_template = Config.GOLDEN_TEMPLATE_3MF
            base_project_cfg = {}
            golden_slice_info = None
            golden_filament_seq = None

            if os.path.exists(golden_template) and zipfile.is_zipfile(golden_template):
                try:
                    with zipfile.ZipFile(golden_template, 'r') as zg:
                        if 'Metadata/project_settings.config' in zg.namelist():
                            base_project_cfg = json.loads(zg.read('Metadata/project_settings.config').decode('utf-8'))
                        if 'Metadata/slice_info.config' in zg.namelist():
                            golden_slice_info = zg.read('Metadata/slice_info.config')
                        if 'Metadata/filament_sequence.json' in zg.namelist():
                            golden_filament_seq = zg.read('Metadata/filament_sequence.json')
                except Exception:
                    pass

            # 2. Build verified strategy overrides
            config_overrides = StrategyOptimizer.build_slicer_overrides(
                mode="split" if len(arranged_meshes) > 1 else mode,
                filament=filament
            )
            config_overrides["printer_model"] = "Bambu Lab A1"
            if custom_overrides:
                config_overrides.update(custom_overrides)

            # Merge overrides onto base project settings (preserving all native Bambu Studio keys)
            full_project_cfg = dict(base_project_cfg) if base_project_cfg else {}
            full_project_cfg.update(config_overrides)

            # Enforce Tree Slim support configuration
            full_project_cfg["enable_support"] = "1"
            full_project_cfg["support_type"] = "tree(auto)"
            full_project_cfg["support_style"] = "tree_slim"
            full_project_cfg["support_top_z_distance"] = str(config_overrides.get("support_top_z_distance", "0.24"))
            full_project_cfg["support_object_xy_distance"] = str(config_overrides.get("support_object_xy_distance", "0.60"))
            full_project_cfg["support_interface_top_layers"] = str(config_overrides.get("support_interface_top_layers", "2"))
            full_project_cfg["curr_bed_type"] = "textured_plate"
            full_project_cfg["filament_is_support"] = ["0", "0"]

            # 3. Prepare slice_info.config with Bambu Studio client signature
            if not golden_slice_info:
                slice_info_xml = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<config>\n'
                    '  <header>\n'
                    '    <header_item key="X-BBL-Client-Type" value="slicer"/>\n'
                    '    <header_item key="X-BBL-Client-Version" value="02.08.02.61"/>\n'
                    '  </header>\n'
                    '</config>'
                ).encode('utf-8')
            else:
                slice_info_xml = golden_slice_info

            # 4. Prepare Metadata/plate_1.json with actual mesh bounding boxes
            import numpy as np
            all_bounds = np.vstack([m.bounds for m in arranged_meshes])
            min_x, min_y = round(float(all_bounds[:, 0].min()), 2), round(float(all_bounds[:, 1].min()), 2)
            max_x, max_y = round(float(all_bounds[:, 0].max()), 2), round(float(all_bounds[:, 1].max()), 2)

            bbox_objects = []
            objs_xml = ""
            instances_xml = ""

            for idx, m in enumerate(arranged_meshes):
                p_source = parts[idx] if idx < len(parts) else f"Part_{idx + 1}.stl"
                p_name = os.path.basename(p_source) if isinstance(p_source, str) else f"Part_{idx + 1}.stl"
                m_min_x, m_min_y = round(float(m.bounds[0][0]), 2), round(float(m.bounds[0][1]), 2)
                m_max_x, m_max_y = round(float(m.bounds[1][0]), 2), round(float(m.bounds[1][1]), 2)

                bbox_objects.append({
                    "area": round(float(m.area), 2),
                    "bbox": [m_min_x, m_min_y, m_max_x, m_max_y],
                    "id": idx + 1,
                    "layer_height": float(full_project_cfg.get("layer_height", 0.12)),
                    "name": p_name
                })

                objs_xml += f"""  <object id="{idx + 1}">
    <metadata key="name" value="{p_name}"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{p_name}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="{p_name}"/>
    </part>
  </object>\n"""

                instances_xml += f"""    <model_instance>
      <metadata key="object_id" value="{idx + 1}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{idx + 1}"/>
    </model_instance>\n"""

            plate_1_data = {
                "bbox_all": [min_x, min_y, max_x, max_y],
                "bbox_objects": bbox_objects,
                "bed_type": "textured_plate",
                "filament_colors": [],
                "filament_ids": [],
                "first_extruder": 0,
                "first_layer_time": 60.0,
                "is_seq_print": False,
                "nozzle_diameter": 0.4,
                "version": 2
            }

            # 5. Build model_settings.config XML
            model_settings_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
{objs_xml}  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
{instances_xml}  </plate>
</config>"""

            # 6. Filament sequence JSON
            if not golden_filament_seq:
                filament_seq_bytes = json.dumps({"plate_1": {"nozzle_sequence": [], "optimal_assignment": [], "sequence": []}}).encode('utf-8')
            else:
                filament_seq_bytes = golden_filament_seq

            os.makedirs(os.path.dirname(os.path.abspath(output_3mf)), exist_ok=True)

            with zipfile.ZipFile(temp_raw_3mf, 'r') as z_in, zipfile.ZipFile(output_3mf, 'w', zipfile.ZIP_DEFLATED) as z_out:
                # 1. Copy verified Bambu relationships, content types, and plate thumbnails from golden template
                copied_golden = set()
                if os.path.exists(golden_template) and zipfile.is_zipfile(golden_template):
                    try:
                        with zipfile.ZipFile(golden_template, 'r') as zg:
                            for f in [
                                '_rels/.rels',
                                '[Content_Types].xml',
                                'Metadata/plate_1.png',
                                'Metadata/plate_1_small.png',
                                'Metadata/plate_no_light_1.png',
                                'Metadata/top_1.png',
                                'Metadata/pick_1.png',
                                'Metadata/cut_information.xml'
                            ]:
                                if f in zg.namelist():
                                    z_out.writestr(f, zg.read(f))
                                    copied_golden.add(f)
                    except Exception:
                        pass

                # 2. Process items from trimesh raw export and inject Bambu Studio application headers
                for item in z_in.infolist():
                    # Skip files already written from golden template
                    if item.filename in copied_golden or item.filename in ['_rels/.rels', '[Content_Types].xml']:
                        continue

                    if item.filename == '3D/3dmodel.model':
                        model_xml = z_in.read(item.filename).decode('utf-8')
                        # Ensure BambuStudio namespace is declared
                        if 'xmlns:BambuStudio=' not in model_xml:
                            model_xml = re.sub(
                                r'<model\s+([^>]+)>',
                                r'<model \1 xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">',
                                model_xml,
                                count=1
                            )
                        # Inject Bambu Studio metadata tags required for native project detection (is_bbl_3mf)
                        bambu_metadata = (
                            '\n <metadata name="Application">BambuStudio-02.08.02.61</metadata>'
                            '\n <metadata name="BambuStudio:3mfVersion">1</metadata>'
                            '\n <metadata name="CreationDate">2026-11-07</metadata>'
                            '\n <metadata name="ModificationDate">2026-11-07</metadata>\n'
                        )
                        model_xml = re.sub(
                            r'(<model\s+[^>]+>)',
                            r'\1' + bambu_metadata,
                            model_xml,
                            count=1
                        )
                        z_out.writestr('3D/3dmodel.model', model_xml.encode('utf-8'))
                    else:
                        z_out.writestr(item, z_in.read(item.filename))

                # Inject complete Bambu Studio project metadata bundle
                z_out.writestr('Metadata/slice_info.config', slice_info_xml)
                z_out.writestr('Metadata/project_settings.config', json.dumps(full_project_cfg, indent=4))
                z_out.writestr('Metadata/model_settings.config', model_settings_xml)
                z_out.writestr('Metadata/plate_1.json', json.dumps(plate_1_data, indent=4))
                z_out.writestr('Metadata/filament_sequence.json', filament_seq_bytes)

            # Validate generated package
            valid, errs = SlicerValidator.validate_package(output_3mf)
            if not valid:
                raise SlicerIntegrationError(f"Generated 3MF failed validation: {'; '.join(errs)}")

            return os.path.abspath(output_3mf)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


