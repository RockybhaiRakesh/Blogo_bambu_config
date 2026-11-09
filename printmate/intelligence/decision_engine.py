"""
Autonomous AI Decision Engine for 3D Printing Strategy.
Synthesizes vision classification, 3D semantic detection, and geometry intelligence
into ranked execution plans, prompting the user only when strategic ambiguity exists.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from printmate.vision.vision_classifier import VisionClassification
from printmate.vision.semantic_detector import SemanticDetectionReport
from printmate.geometry.overhang_analyzer import OverhangReport
from printmate.intelligence.fragility_analyzer import FragilityReport
from printmate.optimization.strategy_optimizer import StrategyOptimizer

if TYPE_CHECKING:
    from printmate.splitting.semantic_split_planner import SemanticSplitPlan, SplitStrategyOption

@dataclass
class UserDecisionQuestion:
    """A structured decision prompt presented when multiple viable strategies compete."""
    question_id: str
    prompt: str
    options: List[str]
    recommended_option: str
    reason: str

@dataclass
class StrategicPrintPlan:
    """Complete ranked printing strategy package."""
    selected_strategy_name: str
    confidence: float                        # 0.0 to 1.0
    ranked_strategies: List[Dict[str, Any]]
    estimated_support_needs: str             # "None", "Minimal Tree", "Extensive Support"
    fragility_risks_summary: str
    assembly_complexity: str                 # "None (1-Piece)", "Low (Snap Dowel)", "High"
    user_decision_required: bool = False
    pending_questions: List[UserDecisionQuestion] = field(default_factory=list)
    slicer_profile_overrides: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

class DecisionEngine:
    """Synthesizes high-level print strategy decisions from vision and geometry inputs."""

    @classmethod
    def evaluate(
        cls,
        classification: VisionClassification,
        semantic_report: SemanticDetectionReport,
        split_plan: Any,
        overhang_report: Optional[OverhangReport] = None,
        fragility_report: Optional[FragilityReport] = None,
        filament: str = "pla_basic"
    ) -> StrategicPrintPlan:
        """
        Synthesizes visual and physical metrics into an authoritative print plan.
        """
        top_split_strategy = split_plan.recommended_strategy
        confidence = round(classification.confidence * 0.95, 2)

        # Build list of ranked strategies
        ranked: List[Dict[str, Any]] = []
        for opt in split_plan.ranked_options:
            ranked.append({
                "name": opt.name,
                "strategy_type": opt.strategy_type,
                "score": opt.score,
                "pros": opt.pros,
                "cons": opt.cons,
                "dowel_feasible": opt.dowel_connector_feasible,
                "support_reduction": f"{opt.estimated_support_reduction_pct:.0f}%"
            })

        # Assess fragility and support needs
        if top_split_strategy.strategy_type in ("semantic_split", "hybrid_split"):
            support_needs = "Minimal Tree (Under upper limbs only)"
            assembly_complexity = "Low (Self-aligning dowel pin joint)"
            mode_slicer = "split"
        elif split_plan.model_exceeds_bed:
            support_needs = "Moderate"
            assembly_complexity = "Medium (Planar joinery required)"
            mode_slicer = "split"
        else:
            support_needs = "Full Tree Supports (Overhang coverage required)"
            assembly_complexity = "None (Single complete piece)"
            mode_slicer = "single"

        fragility_summary = (
            f"Vulnerability Score: {fragility_report.fragility_risk_score:.1f}/10. "
            f"Delicate appendages detected: {'Yes (Hands/Fingers)' if semantic_report.has_delicate_anatomy else 'No'}."
        ) if fragility_report else "Baseline physical risk."

        # Compute slicer profile overrides
        slicer_overrides = StrategyOptimizer.build_slicer_overrides(
            mode=mode_slicer,
            filament=filament
        )

        # Check if user interaction is warranted
        user_questions: List[UserDecisionQuestion] = []
        decision_needed = False

        # If top 2 options have scores within 5 points of each other (e.g. Single vs Split trade-off)
        if len(split_plan.ranked_options) >= 2:
            score_diff = abs(split_plan.ranked_options[0].score - split_plan.ranked_options[1].score)
            if score_diff < 12.0 and not split_plan.model_exceeds_bed:
                decision_needed = True
                user_questions.append(UserDecisionQuestion(
                    question_id="split_vs_single",
                    prompt=(
                        f"Your model contains delicate features ({'hands/ornaments' if semantic_report.has_delicate_anatomy else 'overhangs'}). "
                        "Would you prefer printing in 2 parts without support scarring, or as a single piece with tree supports?"
                    ),
                    options=[
                        "Hybrid Split with Dowel Lock (Recommended - Zero support scarring, clean assembly)",
                        "Single Piece with Safe Tree Supports (Zero assembly, 0.24mm air gap enforced)"
                    ],
                    recommended_option="Hybrid Split with Dowel Lock (Recommended - Zero support scarring, clean assembly)",
                    reason="Prevents support scarring on lotus pedestal and avoids finger breakage during post-processing."
                ))

        return StrategicPrintPlan(
            selected_strategy_name=top_split_strategy.name,
            confidence=confidence,
            ranked_strategies=ranked,
            estimated_support_needs=support_needs,
            fragility_risks_summary=fragility_summary,
            assembly_complexity=assembly_complexity,
            user_decision_required=decision_needed,
            pending_questions=user_questions,
            slicer_profile_overrides=slicer_overrides,
            rationale=top_split_strategy.rationale
        )
