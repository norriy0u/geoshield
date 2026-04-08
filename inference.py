"""
GeoShield Baseline Inference Script
===================================
Runs the LLM agent against all 3 tasks (10 cases each) and emits
strict OpenEnv stdout logs.

Usage:
    python inference.py

Required env vars:
    HF_TOKEN or API_KEY   — your API key
    API_BASE_URL          — defaults to HuggingFace router
    MODEL_NAME            — defaults to Qwen2.5-72B-Instruct
    GEOSHIELD_SERVER_URL  — URL of running GeoShield server (default: http://localhost:7860)
"""

import os
import textwrap
from typing import List, Optional

from openai import OpenAI
from src.geoshield.env_client import GeoShieldEnvClient
from src.geoshield.models import GeoShieldAction

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL = os.getenv("GEOSHIELD_SERVER_URL", "http://localhost:7860")
BENCHMARK = "geoshield"

MAX_STEPS = 3          # per episode / case
CASES_PER_TASK = 10    # evaluate 10 cases per task
TEMPERATURE = 0.3
MAX_TOKENS = 80
SUCCESS_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent("""
    You are an elite SIGINT intelligence analyst.
    You will receive a field observation and situational context.
    Output ONLY ONE action keyword from the valid actions list — no quotes, no punctuation, no explanation.

    Task 1 valid actions: no_anomaly, flag_for_review, escalate_immediately
    Task 2 valid actions: benign, suspicious, hostile, critical
    Task 3 valid actions: monitor, deploy_surveillance, alert_command, immediate_intercept
""").strip()


# --- Mandatory log formatters (DO NOT CHANGE format) ---

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# --- LLM call ---

def get_model_action(client: OpenAI, observation: str, context: str, task_id: int) -> str:
    user_prompt = f"Task: {task_id}\nObservation: {observation}\nContext: {context}\nChoose your action:"
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip().lower().split()[0]
        return text
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return "monitor"


# --- Run one task ---

def run_task(client: OpenAI, env: GeoShieldEnvClient, task_id: int) -> float:
    task_names = {1: "anomaly_detection", 2: "threat_attribution", 3: "response_recommendation"}
    task_name = task_names[task_id]

    all_scores = []

    for case_num in range(CASES_PER_TASK):
        rewards: List[float] = []
        steps_taken = 0
        score = 0.0
        success = False

        log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

        try:
            result = env.reset(task_id=task_id)
            obs = result.observation

            for step in range(1, MAX_STEPS + 1):
                action_str = get_model_action(client, obs.text, obs.context, task_id)
                action = GeoShieldAction(action=action_str)

                step_result = env.step(action)
                reward = step_result.reward
                done = step_result.done
                error = None

                rewards.append(reward)
                steps_taken = step

                log_step(step=step, action=action_str, reward=reward, done=done, error=error)

                if done:
                    obs = step_result.observation
                    break
                obs = step_result.observation

            score = sum(rewards) / len(rewards) if rewards else 0.0
            score = min(max(score, 0.0), 1.0)
            success = score >= SUCCESS_THRESHOLD

        except Exception as e:
            print(f"[DEBUG] Case error: {e}", flush=True)
            success = False
            score = 0.0

        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
        all_scores.append(score)

    avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(f"[TASK_SUMMARY] task={task_name} avg_score={avg:.3f} cases={len(all_scores)}", flush=True)
    return avg


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = GeoShieldEnvClient(base_url=SERVER_URL)

    print(f"[INFO] Connecting to GeoShield server at {SERVER_URL}", flush=True)

    task_scores = []
    for task_id in [1, 2, 3]:
        avg = run_task(client, env, task_id)
        task_scores.append(avg)

    overall = sum(task_scores) / len(task_scores)
    print(f"[FINAL] overall_score={overall:.3f} task_scores={','.join(f'{s:.3f}' for s in task_scores)}", flush=True)

    env.close()


if __name__ == "__main__":
    main()
