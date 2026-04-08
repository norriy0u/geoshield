"""
Programmatic graders for Tasks 1, 2, 3.
Each returns a float score in [0.0, 1.0] with partial credit logic.
"""
from typing import Dict, Any
from models import GeoShieldAction, GeoReward

TASK1_PROXIMITY = {
    "no_anomaly":           {"no_anomaly": 1.0, "flag_for_review": 0.2, "escalate_immediately": 0.0},
    "flag_for_review":      {"flag_for_review": 1.0, "no_anomaly": 0.1, "escalate_immediately": 0.4},
    "escalate_immediately": {"escalate_immediately": 1.0, "flag_for_review": 0.4, "no_anomaly": 0.0},
}

TASK2_PROXIMITY = {
    "benign":     {"benign": 1.0, "suspicious": 0.2, "hostile": 0.0, "critical": 0.0},
    "suspicious": {"suspicious": 1.0, "benign": 0.2, "hostile": 0.3, "critical": 0.0},
    "hostile":    {"hostile": 1.0, "critical": 0.4, "suspicious": 0.2, "benign": 0.0},
    "critical":   {"critical": 1.0, "hostile": 0.4, "suspicious": 0.0, "benign": 0.0},
}

TASK3_PROXIMITY = {
    "monitor":             {"monitor": 1.0, "deploy_surveillance": 0.4, "alert_command": 0.1, "immediate_intercept": 0.0},
    "deploy_surveillance": {"deploy_surveillance": 1.0, "monitor": 0.3, "alert_command": 0.3, "immediate_intercept": 0.0},
    "alert_command":       {"alert_command": 1.0, "deploy_surveillance": 0.3, "immediate_intercept": 0.4, "monitor": 0.0},
    "immediate_intercept": {"immediate_intercept": 1.0, "alert_command": 0.4, "deploy_surveillance": 0.1, "monitor": 0.0},
}

def _base_grade(action_str: str, case: Dict[str, Any], proximity_map: Dict) -> GeoReward:
    gold = case.get("gold_action", "")
    action_str = action_str.strip().lower()

    if gold not in proximity_map:
        return GeoReward(score=0.0, feedback=f"Unknown gold action: {gold}")

    score = proximity_map[gold].get(action_str, 0.0)

    # Difficulty multiplier — hard cases give more signal
    difficulty = case.get("difficulty", "easy")
    if difficulty == "hard" and score > 0.0 and score < 1.0:
        score = round(score * 0.9, 3)  # slightly stricter on hard cases

    if score >= 0.9:
        feedback = f"Correct. Gold: {gold}."
    elif score >= 0.3:
        feedback = f"Partial credit ({score:.2f}). You chose '{action_str}', gold was '{gold}'."
    else:
        feedback = f"Incorrect. You chose '{action_str}', gold was '{gold}'."

    return GeoReward(
        score=round(score, 3),
        feedback=feedback,
        breakdown={
            "gold_action": gold,
            "agent_action": action_str,
            "category": case.get("category", ""),
            "difficulty": difficulty,
            "score": score,
        }
    )

def grade_task1(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    return _base_grade(action.action, case, TASK1_PROXIMITY)

def grade_task2(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    return _base_grade(action.action, case, TASK2_PROXIMITY)

def grade_task3(action: GeoShieldAction, case: Dict[str, Any]) -> GeoReward:
    base = _base_grade(action.action, case, TASK3_PROXIMITY)

    # Reasoning quality bonus (up to +0.15)
    if action.reasoning:
        reasoning = action.reasoning.strip()
        bonus = 0.0
        if len(reasoning) > 20:
            bonus += 0.05
        if len(reasoning) > 80:
            bonus += 0.05
        # Extra bonus if reasoning mentions key threat keywords
        keywords = ["frequency", "pattern", "threat", "signal", "intercept", "hostile", "risk", "anomaly"]
        matches = sum(1 for kw in keywords if kw in reasoning.lower())
        if matches >= 2:
            bonus += 0.05
        bonus = round(min(0.15, bonus), 3)
        base.score = round(min(1.0, base.score + bonus), 3)
        if bonus > 0:
            base.feedback += f" Reasoning bonus: +{bonus:.2f}"

    return base

GRADERS = {
    1: grade_task1,
    2: grade_task2,
    3: grade_task3,
}
