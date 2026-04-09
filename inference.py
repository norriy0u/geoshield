"""
GeoShield Baseline Inference Script
"""
import os
import sys
import textwrap
from typing import List, Optional

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

try:
    from openai import OpenAI
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
    from openai import OpenAI

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL = os.getenv("GEOSHIELD_SERVER_URL", "https://norriy0u-geoshield.hf.space")
BENCHMARK = "geoshield"
MAX_STEPS = 3
SUCCESS_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent("""
    You are an elite SIGINT intelligence analyst.
    Output ONLY ONE action keyword from the valid actions list — no quotes, no punctuation.
    Task 1 valid actions: no_anomaly, flag_for_review, escalate_immediately
    Task 2 valid actions: benign, suspicious, hostile, critical
    Task 3 valid actions: monitor, deploy_surveillance, alert_command, immediate_intercept
""").strip()

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

def get_model_action(client, observation, task_id):
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Task: {task_id}\nObservation: {observation}\nChoose your action:"},
            ],
            temperature=0.3,
            max_tokens=20,
        )
        return (completion.choices[0].message.content or "").strip().lower().split()[0]
    except Exception as e:
        print(f"[DEBUG] LLM error: {e}", flush=True)
        return "monitor"

def run_task(client, task_id):
    task_names = {1: "anomaly_detection", 2: "threat_attribution", 3: "response_recommendation"}
    task_name = task_names[task_id]
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        r = requests.post(f"{SERVER_URL}/reset", json={"task_id": task_id}, timeout=30)
        result = r.json()
        obs = result.get("observation", {})
        obs_text = str(obs.get("signal_data", obs.get("text", str(obs))))

        for step in range(1, MAX_STEPS + 1):
            action_str = get_model_action(client, obs_text, task_id)

            r = requests.post(f"{SERVER_URL}/step", json={"action": action_str}, timeout=30)
            step_result = r.json()

            reward = float(step_result.get("reward", 0.0))
            done = bool(step_result.get("done", False))
            error = step_result.get("error", None)

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            if done:
                break

            obs = step_result.get("observation", {})
            obs_text = str(obs.get("signal_data", obs.get("text", str(obs))))

        score = sum(rewards) / len(rewards) if rewards else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Task error: {e}", flush=True)

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return score

def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    scores = []
    for task_id in [1, 2, 3]:
        s = run_task(client, task_id)
        scores.append(s)
    overall = sum(scores) / len(scores)
    print(f"[FINAL] overall_score={overall:.3f}", flush=True)

if __name__ == "__main__":
    main()
