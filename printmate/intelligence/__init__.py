"""
Intelligence package for PrintMate AI.
Contains risk assessment, scale classification, fragility analysis, and strategic AI decision engine.
"""

from printmate.intelligence.classification import ClassificationEngine
from printmate.intelligence.risk_assessment import RiskAssessor
from printmate.intelligence.fragility_analyzer import FragilityAnalyzer, FragilityReport, FragileFeature
from printmate.intelligence.decision_engine import DecisionEngine, StrategicPrintPlan, UserDecisionQuestion

__all__ = [
    "ClassificationEngine",
    "RiskAssessor",
    "FragilityAnalyzer",
    "FragilityReport",
    "FragileFeature",
    "DecisionEngine",
    "StrategicPrintPlan",
    "UserDecisionQuestion"
]
