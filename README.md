# 🛡️ GeoShield: SIGINT Triage Benchmark

**Autonomous Signals Intelligence Monitoring & Response Environment**  
*Built for the OpenEnv Hackathon*

[![Live Demo](https://img.shields.io/badge/🤗%20HF%20Space-Live-green)](https://huggingface.co/spaces/norriy0u/geoshield)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-blue)]()

GeoShield simulates the role of a **Signals Intelligence (SIGINT) analyst**, requiring agents to detect, attribute, and respond to electronic threats in real-time. It models a genuine high-stakes triage workflow used in cybersecurity and defense intelligence operations.

---

## 🎯 Environment Description

Modern SIGINT analysts are overwhelmed with signal data — most of it noise. GeoShield challenges agents to act as a first-line analyst: filter suspicious signals, attribute them to known threat actors, and recommend the correct tactical response under time pressure. This mirrors real analyst workflows in SOC (Security Operations Center) environments.

---

## 📋 Tasks

| Task | Name | Difficulty | Description |
|------|------|------------|-------------|
| 1 | **Anomaly Detection** | Easy | Identify which signals in a noisy feed are anomalous based on frequency, power, and timing patterns |
| 2 | **Threat Attribution** | Medium | Given anomalous signal metadata, identify the threat actor origin and intent from known signatures |
| 3 | **Response Recommendation** | Hard | Recommend the correct tactical action (Intercept / Escalate / Monitor) with mandatory chain-of-thought reasoning |

---

## 🔭 Observation Space

Each observation contains:

| Field | Type | Description |
|-------|------|-------------|
| `signal_id` | string | Unique identifier for the current signal |
| `frequency_mhz` | float | Signal frequency in MHz |
| `power_dbm` | float | Signal power in dBm |
| `modulation` | string | Modulation type (AM/FM/PSK/QAM) |
| `duration_ms` | int | Signal duration in milliseconds |
| `metadata` | dict | Additional context (location hints, pattern history) |
| `task_id` | int | Current task (1, 2, or 3) |
| `step` | int | Current step number in episode |

---

## ⚡ Action Space

| Task | Valid Actions |
|------|--------------|
| Task 1 | `"anomalous"` or `"normal"` |
| Task 2 | `"state_actor"`, `"criminal"`, `"unknown"`, `"friendly"` |
| Task 3 | `"intercept"`, `"escalate"`, `"monitor"` (+ optional `reasoning` field) |

Actions are submitted as JSON: `{"action": "anomalous"}` or `{"action": "escalate", "reasoning": "High-power PSK burst matches known APT signature"}`

---

## 📈 Reward Function

GeoShield uses a **Deterministic Strategic Grader** with partial credit:

- **Full credit (1.0)**: Optimal action matching ground truth
- **Partial credit (0.3–0.5)**: Cautious/secondary-best actions that prioritize safety
- **Reasoning bonus (+0.1)**: Task 3 responses with substantive reasoning (>20 chars)
- **Step penalty**: Slight decay for excessive steps in time-sensitive cases
- **Range**: All scores clamped to `[0.0, 1.0]`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start new episode. Body: `{"task_id": 1, "seed": null}` |
| `POST` | `/step` | Take action. Body: `{"action": "anomalous", "reasoning": null}` |
| `GET` | `/state` | Get current environment state |
| `GET` | `/health` | Health check |

**Base URL:** `https://norriy0u-geoshield.hf.space`

---

## 🚀 Setup & Usage

### Option 1: Use the Live HF Space

```bash
export GEOSHIELD_SERVER_URL="https://norriy0u-geoshield.hf.space"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_hf_token_here"

python inference.py
```

### Option 2: Run Locally with Docker

```bash
git clone https://github.com/norriy0u/geoshield
cd geoshield
docker build -t geoshield .
docker run -p 7860:7860 geoshield
```

Then set `GEOSHIELD_SERVER_URL=http://localhost:7860` and run `python inference.py`.

---

## 📊 Baseline Scores

Baseline run using `Qwen/Qwen2.5-72B-Instruct` via HF Inference Router:

| Task | Difficulty | Baseline Score |
|------|------------|---------------|
| Task 1 — Anomaly Detection | Easy | ~0.72 |
| Task 2 — Threat Attribution | Medium | ~0.51 |
| Task 3 — Response Recommendation | Hard | ~0.38 |

---

## 🗂️ Project Structure

```
geoshield/
├── app.py                # FastAPI server (/reset, /step, /state, /health)
├── environment.py        # Core OpenEnv environment logic
├── models.py             # Pydantic models (Action, Observation, State, Reward)
├── graders.py            # Deterministic task graders
├── inference.py          # Baseline inference script (OpenAI client)
├── openenv.yaml          # OpenEnv spec metadata
├── Dockerfile            # Container definition
├── task1_train.jsonl     # Task 1 training data
├── task2_train.jsonl     # Task 2 training data
└── task3_train.jsonl     # Task 3 training data
```
## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `HF_TOKEN` | — | Hugging Face API key |
| `GEOSHIELD_SERVER_URL` | `https://norriy0u-geoshield.hf.space` | Environment server URL |
