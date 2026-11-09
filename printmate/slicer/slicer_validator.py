"""
Slicer project validation module.
Verifies structure, integrity, and config syntax of Bambu Studio .3mf archives.
"""

import os
import zipfile
import json
from typing import List, Tuple
from printmate.core.exceptions import SlicerIntegrationError

class SlicerValidator:
    """Validates generated .3mf packages and internal config files."""

    REQUIRED_METADATA_FILES = [
        "Metadata/project_settings.config",
        "Metadata/model_settings.config"
    ]

    @classmethod
    def validate_package(cls, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validates that a .3mf file is a valid zip archive and contains required Bambu configs.

        Args:
            file_path: Path to the .3mf file.

        Returns:
            Tuple of (is_valid, list_of_error_strings).
        """
        errors: List[str] = []

        if not os.path.exists(file_path):
            return False, [f"File does not exist: {file_path}"]

        if not zipfile.is_zipfile(file_path):
            return False, [f"File is not a valid zip archive: {file_path}"]

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                namelist = zf.namelist()

                # Check for critical configs
                for req in cls.REQUIRED_METADATA_FILES:
                    if req not in namelist:
                        errors.append(f"Missing mandatory Bambu metadata: {req}")

                # Validate JSON syntax of project_settings.config if present
                if "Metadata/project_settings.config" in namelist:
                    try:
                        raw = zf.read("Metadata/project_settings.config").decode('utf-8')
                        data = json.loads(raw)
                        if not isinstance(data, dict):
                            errors.append("project_settings.config is not a valid JSON dictionary")
                    except Exception as e:
                        errors.append(f"Failed to parse project_settings.config: {str(e)}")

        except Exception as e:
            errors.append(f"Archive inspection failed: {str(e)}")

        return (len(errors) == 0), errors

