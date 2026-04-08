"""
Core GeoShieldEnvironment class — episodic decision RL environment.
Each episode = one case from the JSONL data for the given task.
Episode ends after the agent submits one action (single-step decision).
"""
import time
from typing import Optional, Tuple, Dict, Any

from ..models import GeoShieldAction, GeoObservation, GeoReward, GeoState
from ..constants import TASK_ACTIONS, TASK_DESCRIPTIONS
from .generators import sample_case
from .graders import GRADERS
from .rewards import compute_reward

MAX_STEPS = {1: 3, 2: 3, 3: 5}  # Task 3 allows re-evaluation steps


class GeoShieldEnvironment:
    def __init__(self):
        self._state: Optional[GeoState] = None
        self._current_case: Optional[Dict[str, Any]] = None
        self._task_id: int = 1

    def reset(self, task_id: int = 1, seed: int = None) -> Tuple[GeoObservation, GeoState]:
        self._task_id = task_id
        case = sample_case(task_id, seed=seed)
        self._current_case = case

        self._state = GeoState(
            task_id=task_id,
            case_id=case["id"],
            completed=False,
            step=0,
            rewards=[],
            current_observation=case["observation"],
        )

        obs = GeoObservation(
            text=case["observation"],
            context=case.get("context", ""),
            task_id=task_id,
            case_id=case["id"],
            available_actions=TASK_ACTIONS[task_id],
            step=0,
        )
        return obs, self._state

    def step(self, action: GeoShieldAction) -> Tuple[GeoObservation, float, bool, Dict[str, Any]]:
        if self._state is None or self._current_case is None:
            raise RuntimeError("Call reset() before step()")

        self._state.step += 1
        step = self._state.step
        max_steps = MAX_STEPS.get(self._task_id, 3)

        # Grade the action
        grader = GRADERS[self._task_id]
        grader_reward: GeoReward = grader(action, self._current_case)
        reward = compute_reward(grader_reward, step, max_steps)

        self._state.rewards.append(reward)

        # Episode ends if: correct answer OR max steps reached
        correct = grader_reward.score >= 0.9
        done = correct or step >= max_steps
        self._state.completed = done

        obs = GeoObservation(
            text=self._current_case["observation"],
            context=self._current_case.get("context", ""),
            task_id=self._task_id,
            case_id=self._current_case["id"],
            available_actions=TASK_ACTIONS[self._task_id],
            step=step,
        )

        info = {
            "grader_score": grader_reward.score,
            "feedback": grader_reward.feedback,
            "breakdown": grader_reward.breakdown,
            "gold_action": self._current_case.get("gold_action"),
            "case_difficulty": self._current_case.get("difficulty"),
            "case_category": self._current_case.get("category"),
        }

        return obs, reward, done, info

    def state(self) -> GeoState:
        if self._state is None:
            return GeoState(task_id=0, case_id="", completed=False, step=0)
        return self._state
