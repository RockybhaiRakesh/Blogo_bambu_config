"""
Bambu Studio application bridge module.
Provides process control and project launching for Bambu Studio.
"""

import os
import subprocess
from typing import Optional
from printmate.core.config import Config
from printmate.core.exceptions import SlicerIntegrationError

class BambuBridge:
    """Interfaces with the Bambu Studio desktop application."""

    @staticmethod
    def launch(project_3mf: str, executable_path: Optional[str] = None) -> bool:
        """
        Launches Bambu Studio with the specified .3mf project file.

        Args:
            project_3mf: Path to the .3mf project file.
            executable_path: Optional path to bambu-studio.exe.

        Returns:
            True if process was spawned successfully.
        """
        exe = executable_path or Config.BAMBU_STUDIO_EXE
        if not os.path.exists(exe):
            raise SlicerIntegrationError(f"Bambu Studio executable not found at: {exe}")

        if not os.path.exists(project_3mf):
            raise SlicerIntegrationError(f"Target project file not found: {project_3mf}")

        try:
            subprocess.Popen([exe, os.path.abspath(project_3mf)])
            return True
        except Exception as e:
            raise SlicerIntegrationError(f"Could not launch Bambu Studio: {str(e)}") from e

    @staticmethod
    def reveal_in_explorer(file_path: str) -> None:
        """
        Opens Windows Explorer with the specified file selected.
        """
        if os.path.exists(file_path):
            subprocess.Popen(["explorer.exe", f"/select,{os.path.abspath(file_path)}"])

