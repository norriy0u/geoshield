from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class GeoShieldAction(BaseModel):
    action: str
    reasoning: Optional[str] = None


class GeoObservation(BaseModel):
    text: str
    context: str
    task_id: int
    case_id: str
    available_actions: List[str]
    step: int = 0


class GeoReward(BaseModel):
    score: float
    feedback: str
    breakdown: Optional[Dict[str, Any]] = None


class GeoState(BaseModel):
    task_id: int
    case_id: str
    completed: bool
    step: int
    rewards: List[float] = []
    current_observation: Optional[str] = None
