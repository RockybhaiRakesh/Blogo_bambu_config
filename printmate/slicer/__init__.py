"""
Slicer integration package for PrintMate AI.
Handles Bambu Studio project generation, settings patching, and bridge execution.
"""

from printmate.slicer.slicer_validator import SlicerValidator
from printmate.slicer.project_generator import BambuProjectGenerator
from printmate.slicer.bambu_bridge import BambuBridge
from printmate.slicer.slicer_bridge import SlicerBridge, SlicingResult

__all__ = ["SlicerValidator", "BambuProjectGenerator", "BambuBridge", "SlicerBridge", "SlicingResult"]
