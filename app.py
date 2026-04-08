"""
GeoShield FastAPI server — exposes /reset, /step, /state, /health endpoints.
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models import GeoShieldAction, GeoObservation, GeoState
from environment import GeoShieldEnvironment
app = FastAPI(title="GeoShield OpenEnv", version="1.0.0")

# One global env instance per process (fine for hackathon single-agent use)
_env = GeoShieldEnvironment()


# --- Request/Response schemas ---

class ResetRequest(BaseModel):
    task_id: int = 1
    seed: Optional[int] = None


class StepRequest(BaseModel):
    action: str
    reasoning: Optional[str] = None


class StepResponse(BaseModel):
    observation: GeoObservation
    reward: float
    done: bool
    info: dict


class ResetResponse(BaseModel):
    observation: GeoObservation
    state: GeoState


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok", "env": "geoshield"}


@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest = ResetRequest()):
    obs, state = _env.reset(task_id=req.task_id, seed=req.seed)
    return ResetResponse(observation=obs, state=state)


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    action = GeoShieldAction(action=req.action, reasoning=req.reasoning)
    try:
        obs, reward, done, info = _env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StepResponse(observation=obs, reward=reward, done=done, info=info)


@app.get("/state", response_model=GeoState)
def get_state():
    return _env.state()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("src.geoshield.server.app:app", host="0.0.0.0", port=port, reload=False)
