# 🛡️ GeoShield: SIGINT Triage Benchmark
**Autonomous Signals Intelligence Monitoring & Response Environment**

GeoShield is a high-fidelity reinforcement learning benchmark developed for the **OpenEnv Hackathon**. It simulates the role of a Signals Intelligence (SIGINT) analyst, requiring agents to detect, attribute, and respond to electronic threats in real-time.

## 🎯 Benchmark Objectives
The environment evaluates agents across three sophisticated intelligence tiers:

1. **Tier 1: Anomaly Detection** – Sifting through high-volume signal data to isolate suspicious electronic signatures.
2. **Tier 2: Threat Attribution** – Utilizing signal metadata to identify the origin and intent of the actor.
3. **Tier 3: Response Recommendation** – Recommending tactical actions (Intercept, Escalate, Monitor) with mandatory chain-of-thought reasoning.

## 🧠 Technical Architecture
The system is built on a robust microservice architecture to ensure consistent evaluation in cloud environments:

* **Logic Layer**: A custom Python environment built with the `openenv-core` SDK, managing state transitions and observation generation.
* **API Layer**: A FastAPI-based server providing low-latency communication via REST endpoints (`/reset`, `/step`, `/state`).
* **Deployment**: Fully containerized using **Docker**, optimized for horizontal scaling on **Hugging Face Spaces**.

## 📈 Advanced Scoring Logic
GeoShield distinguishes itself with a **Deterministic Strategic Grader**:

* **Strategic Partial Credit**: Awards partial points (e.g., 0.3 or 0.5) for cautious or secondary-best actions that prioritize safety over binary pass/fail.
* **Reasoning Multiplier**: Agents that provide substantive reasoning in Task 3 receive a **+0.1 bonus**, rewarding "explainable AI".
* **Performance Decay**: Encourages rapid response by slightly penalizing excessive steps in time-sensitive triage cases.

## 🛠️ Quick Start
To interact with the environment, set your server URL and run the baseline:

```powershell
# Set the server URL to your live Space
$env:GEOSHIELD_SERVER_URL="[https://norriy0u-geoshield.hf.space](https://norriy0u-geoshield.hf.space)"

# Run the evaluation baseline
python inference.py
