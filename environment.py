"""
Core GeoShieldEnvironment — episodic RL environment for SIGINT triage.
"""
from typing import Optional, Tuple, Dict, Any
from models import GeoShieldAction, GeoObservation, GeoReward, GeoState, SignalMetadata
from graders import GRADERS

TASK_ACTIONS = {
    1: ["no_anomaly", "flag_for_review", "escalate_immediately"],
    2: ["benign", "suspicious", "hostile", "critical"],
    3: ["monitor", "deploy_surveillance", "alert_command", "immediate_intercept"],
}

MAX_STEPS = {1: 3, 2: 3, 3: 5}

import json, random, pathlib, os

def load_cases(task_id: int):
    path = pathlib.Path(__file__).parent / f"task{task_id}_train.jsonl"
    if not path.exists():
        path = pathlib.Path(f"task{task_id}_train.jsonl")
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases

def sample_case(task_id: int, seed=None):
    cases = load_cases(task_id)
    rng = random.Random(seed)
    return rng.choice(cases)

def compute_reward(grader_reward: GeoReward, step: int, max_steps: int) -> float:
    base = grader_reward.score
    # Step penalty: lose up to 0.1 for being slow
    step_penalty = 0.0
    if step > 1:
        step_penalty = min(0.1, (step - 1) * 0.03)
    reward = max(0.0, base - step_penalty)
    return round(reward, 3)

class GeoShieldEnvironment:
    def __init__(self):
        self._state: Optional[GeoState] = None
        self._current_case: Optional[Dict[str, Any]] = None
        self._task_id: int = 1

    def reset(self, task_id: int = 1, seed: int = None) -> Tuple[GeoObservation, GeoState]:
        self._task_id = task_id
        case = sample_case(task_id, seed=seed)
        self._current_case = case
        difficulty = case.get("difficulty", "easy")

        self._state = GeoState(
            task_id=task_id,
            case_id=case["id"],
            completed=False,
            step=0,
            rewards=[],
            current_observation=case["observation"],
            total_score=0.0,
            difficulty=difficulty,
        )

        # Build rich signal metadata if available
        sig_meta = None
        if "signal_metadata" in case:
            m = case["signal_metadata"]
            sig_meta = SignalMetadata(
                frequency_mhz=m.get("frequency_mhz", 100.0),
                power_dbm=m.get("power_dbm", -60.0),
                modulation=m.get("modulation", "AM"),
                duration_ms=m.get("duration_ms", 500),
                region=m.get("region", "unknown"),
                time_of_day=m.get("time_of_day", "day"),
                repeat_count=m.get("repeat_count", 1),
                known_pattern=m.get("known_pattern"),
            )

        obs = GeoObservation(
            text=case["observation"],
            context=case.get("context", ""),
            task_id=task_id,
            case_id=case["id"],
            available_actions=TASK_ACTIONS[task_id],
            step=0,
            difficulty=difficulty,
            signal_metadata=sig_meta,
            signal_history=case.get("signal_history", []),
            threat_indicators=case.get("threat_indicators", []),
        )
        return obs, self._state

    def step(self, action: GeoShieldAction) -> Tuple[GeoObservation, float, bool, Dict[str, Any]]:
        if self._state is None or self._current_case is None:
            raise RuntimeError("Call reset() before step()")

        self._state.step += 1
        step = self._state.step
        max_steps = MAX_STEPS.get(self._task_id, 3)

        grader = GRADERS[self._task_id]
        grader_reward: GeoReward = grader(action, self._current_case)
        reward = compute_reward(grader_reward, step, max_steps)

        self._state.rewards.append(reward)
        self._state.total_score = round(sum(self._state.rewards) / len(self._state.rewards), 3)

        correct = grader_reward.score >= 0.9
        done = correct or step >= max_steps
        self._state.completed = done

        sig_meta = None
        if "signal_metadata" in self._current_case:
            m = self._current_case["signal_metadata"]
            sig_meta = SignalMetadata(
                frequency_mhz=m.get("frequency_mhz", 100.0),
                power_dbm=m.get("power_dbm", -60.0),
                modulation=m.get("modulation", "AM"),
                duration_ms=m.get("duration_ms", 500),
                region=m.get("region", "unknown"),
                time_of_day=m.get("time_of_day", "day"),
                repeat_count=m.get("repeat_count", 1),
                known_pattern=m.get("known_pattern"),
            )

        obs = GeoObservation(
            text=self._current_case["observation"],
            context=self._current_case.get("context", ""),
            task_id=self._task_id,
            case_id=self._current_case["id"],
            available_actions=TASK_ACTIONS[self._task_id],
            step=step,
            difficulty=self._current_case.get("difficulty", "easy"),
            signal_metadata=sig_meta,
            signal_history=self._current_case.get("signal_history", []),
            threat_indicators=self._current_case.get("threat_indicators", []),
        )

        info = {
            "grader_score": grader_reward.score,
            "feedback": grader_reward.feedback,
            "breakdown": grader_reward.breakdown,
            "gold_action": self._current_case.get("gold_action"),
            "case_difficulty": self._current_case.get("difficulty"),
            "case_category": self._current_case.get("category"),
            "step_penalty_applied": step > 1,
        }
        return obs, reward, done, info

    def state(self) -> GeoState:
        if self._state is None:
            return GeoState(task_id=0, case_id="", completed=False, step=0)
        return self._state
