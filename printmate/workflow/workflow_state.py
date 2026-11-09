"""
Workflow state tracking module.
Maintains state machine transitions and logs execution events.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

class WorkflowStage(str, Enum):
    INITIALIZED = "INITIALIZED"
    FILE_VALIDATION = "FILE_VALIDATION"
    GEOMETRY_ANALYSIS = "GEOMETRY_ANALYSIS"
    MESH_VALIDATION = "MESH_VALIDATION"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    STRATEGY_OPTIMIZATION = "STRATEGY_OPTIMIZATION"
    PROJECT_GENERATION = "PROJECT_GENERATION"
    SLICER_VALIDATION = "SLICER_VALIDATION"
    LAUNCHING_STUDIO = "LAUNCHING_STUDIO"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class WorkflowState:
    """Stores workflow execution state and artifacts."""
    stage: WorkflowStage = WorkflowStage.INITIALIZED
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)

    def transition(self, new_stage: WorkflowStage) -> None:
        """Transitions state to a new stage."""
        self.stage = new_stage

    def record_error(self, message: str) -> None:
        """Records an error and marks workflow as failed."""
        self.errors.append(message)
        self.stage = WorkflowStage.FAILED

    def record_warning(self, message: str) -> None:
        """Records a non-fatal warning."""
        self.warnings.append(message)

    def complete(self) -> None:
        """Marks workflow as successfully completed."""
        self.stage = WorkflowStage.COMPLETED
        self.end_time = time.time()

