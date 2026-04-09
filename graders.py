import sys
sys.path.insert(0, '/app/src/geoshield')
sys.path.insert(0, '/app/src/geoshield/server')
sys.path.insert(0, '/app')
"""
Programmatic graders for Tasks 1, 2, 3.
Each returns a float score strictly in (0.0, 1.0) with partial credit logic.
"""
from typing import Dict, Any
from models import GeoShieldAction, GeoReward

TASK1_PROXIMITY = {
    "no_anomaly":           {"no_anomaly": 0.99, "flag_for_review": 0.2, "escalate_immediately": 0.01},
    "flag_for_review":      {"flag_for_review": 0.99, "no_anomaly": 0.1, "escalate_immediately": 0.4},
    "escalate_immediately": {"escalate_immediately": 0.99, "flag_for_review": 0.4, "no_anomaly": 0.01},
}

TASK2_PROXIMITY = {
    "benign":     {"benign": 0.99, "suspicious": 0.2, "hostile": 0.01, "critical": 0.01},
    "suspicious": {"suspicious": 0.99, "benign": 0.2, "hostile": 0.3, "critical": 0.01},
    "hostile":    {"hostile": 0.99, "critical": 0.4, "suspicious": 0.2, "benign": 0.01},
    "critical":   {"critical": 0.99, "hostile": 0.4, "suspicious": 0.01, "benign": 0.01},
}

TASK3_PROXIMITY = {
    "monitor":             {"monitor": 0.99, "deploy_surveillance": 0.4, "alert_command": 0.1, "immediate_intercept": 0.01},
    "deploy_surveillance": {"deploy_surveillance": 0.99, "monitor": 0.3, "alert_command": 0.3, "immediate_intercept": 0.01},
    "alert_command":       {"alert_command": 0.99, "deploy_surveillance": 0.3, "immediate_intercept": 0.4, "monitor": 0.01},
    "immediate_intercept": {"immediate_intercept": 0.99, "alert_command": 0.4, "deploy_surveillance": 0.1, "monitor": 0.01},
}


def _clamp(score: float) -> float:
    """Score must be strictly between 0 and 1, not 0.0 or 1.0"""
    score = round(score, 3)
    if score <= 0.0:
        return 0.01
    if score >= 1.0:
        return 0.99
    return score


def _base_grade(action_str: str, case: Dict[str, Any], proximity_map: Dict) -> GeoReward:
    gold = case.get("gold_action", "")
    action_str = action_str.strip().lower()

    if gold not in proximity_map:
        return GeoReward(score=0.01, feedback=f"Unknown gold action: {gold}")

    score = proximity_map[gold].get(action_str, 0.01)

    difficulty = case.get("difficulty", "easy")
    if difficulty == "hard" and score > 0.01 and score < 0.99:
        score = round(score * 0.9, 3)

    if score >= 0.9:
        feedback = f"Correct. Gold: {gold}."
    elif score >= 0.3:
        feedback = f"Partial credit ({score:.2f}). You chose '{action_str}', gold was '{gold}'."
    else:
        feedback = f"Incorrect. You chose '{action_str}', gold was '{gold}'."

    return GeoReward(
        score=_clamp(score),
        feedback=feedback,
        breakdown={
            "gold_action": gold,
            "agent_action": action_str,
            "category": case.get("category", ""),
            "difficulty": difficulty,
            "score": _clamp(score),
        }
    )


def grade_task1(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    return _base_grade(action.action, case, TASK1_PROXIMITY)


def grade_task2(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    return _base_grade(action.action, case, TASK2_PROXIMITY)


def grade_task3(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    base = _base_grade(action.action, case, TASK3_PROXIMITY)

    if action.reasoning:
        reasoning = action.reasoning.strip()
        bonus = 0.0
        if len(reasoning) > 20:
            bonus += 0.05
        if len(reasoning) > 80:
            bonus += 0.05
        keywords = ["frequency", "pattern", "threat", "signal", "intercept", "hostile", "risk", "anomaly"]
        matches = sum(1 for kw in keywords if kw in reasoning.lower())
        if matches >= 2:
            bonus += 0.05
        bonus = round(min(0.15, bonus), 3)
        base.score = _clamp(base.score + bonus)
        if bonus > 0:
            base.feedback += f" Reasoning bonus: +{bonus:.2f}"

    return base


GRADERS = {
    1: grade_task1,
    2: grade_task2,
    3: grade_task3,
}
