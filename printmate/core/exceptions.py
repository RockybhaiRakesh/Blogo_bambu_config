"""
Domain exceptions for PRINTMATE AI.
"""

class PrintMateError(Exception):
    """Base exception for all PRINTMATE AI errors."""
    pass

class GeometryLoadError(PrintMateError):
    """Raised when loading a 3D geometry file fails."""
    pass

class MeshValidationError(PrintMateError):
    """Raised when a 3D mesh fails validation checks."""
    pass

class SplitError(PrintMateError):
    """Raised when slicing or bisecting a mesh fails."""
    pass

class SlicerIntegrationError(PrintMateError):
    """Raised when packaging 3MF projects or launching slicers fails."""
    pass

class ConnectorError(PrintMateError):
    """Raised when connector generation fails."""
    pass

class OptimizationError(PrintMateError):
    """Raised when mesh optimization or decimation fails."""
    pass

class MultiSplitError(PrintMateError):
    """Raised when multi-part splitting fails."""
    pass

