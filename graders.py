"""
Programmatic graders for Tasks 1, 2, 3.
Each returns a float score in [0.0, 1.0] with partial credit logic.
"""

from typing import Dict, Any
from ..models import GeoShieldAction, GeoReward
from ..constants import TASK1_ACTIONS, TASK2_ACTIONS, TASK3_ACTIONS

# --- Partial credit maps (how close is a wrong answer?) ---

TASK1_PROXIMITY = {
    # gold -> {action -> score}
    "no_anomaly":           {"no_anomaly": 1.0, "flag_for_review": 0.3, "escalate_immediately": 0.0},
    "flag_for_review":      {"flag_for_review": 1.0, "no_anomaly": 0.2, "escalate_immediately": 0.5},
    "escalate_immediately": {"escalate_immediately": 1.0, "flag_for_review": 0.5, "no_anomaly": 0.0},
}

TASK2_PROXIMITY = {
    "benign":    {"benign": 1.0, "suspicious": 0.3, "hostile": 0.0, "critical": 0.0},
    "suspicious":{"suspicious": 1.0, "benign": 0.3, "hostile": 0.4, "critical": 0.1},
    "hostile":   {"hostile": 1.0, "critical": 0.5, "suspicious": 0.3, "benign": 0.0},
    "critical":  {"critical": 1.0, "hostile": 0.5, "suspicious": 0.1, "benign": 0.0},
}

TASK3_PROXIMITY = {
    "monitor":              {"monitor": 1.0, "deploy_surveillance": 0.5, "alert_command": 0.2, "immediate_intercept": 0.0},
    "deploy_surveillance":  {"deploy_surveillance": 1.0, "monitor": 0.4, "alert_command": 0.4, "immediate_intercept": 0.1},
    "alert_command":        {"alert_command": 1.0, "deploy_surveillance": 0.4, "immediate_intercept": 0.5, "monitor": 0.1},
    "immediate_intercept":  {"immediate_intercept": 1.0, "alert_command": 0.5, "deploy_surveillance": 0.2, "monitor": 0.0},
}

DIFFICULTY_MULTIPLIER = {"easy": 1.0, "medium": 1.0, "hard": 1.0}  # scores are already calibrated


def _base_grade(action_str: str, case: Dict[str, Any], proximity_map: Dict) -> GeoReward:
    gold = case.get("gold_action", "")
    action_str = action_str.strip().lower()
    
    if gold not in proximity_map:
        return GeoReward(score=0.0, feedback=f"Unknown gold action: {gold}")
    
    score = proximity_map[gold].get(action_str, 0.0)
    
    if score == 1.0:
        feedback = f"Correct. Gold: {gold}."
    elif score > 0.3:
        feedback = f"Partial credit. You chose '{action_str}', gold was '{gold}'."
    else:
        feedback = f"Incorrect. You chose '{action_str}', gold was '{gold}'."

    return GeoReward(
        score=score,
        feedback=feedback,
        breakdown={"gold_action": gold, "agent_action": action_str, "category": case.get("category", ""), "difficulty": case.get("difficulty", "")}
    )


def grade_task1(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    return _base_grade(action.action, case, TASK1_PROXIMITY)


def grade_task2(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    return _base_grade(action.action, case, TASK2_PROXIMITY)


def grade_task3(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    # Task 3 is the hard task — also checks reasoning quality for partial bonus
    base = _base_grade(action.action, case, TASK3_PROXIMITY)
    
    # Bonus: if reasoning provided and non-empty, small bonus up to 0.1
    if action.reasoning and len(action.reasoning.strip()) > 20:
        bonus = min(0.1, len(action.reasoning.strip()) / 1000)
        base.score = min(1.0, base.score + bonus)
        base.feedback += f" Reasoning bonus: +{bonus:.2f}"
    
    return base


GRADERS = {
    1: grade_task1,
    2: grade_task2,
    3: grade_task3,
}
