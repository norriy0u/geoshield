from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class GeoShieldAction(BaseModel):
    action: str
    reasoning: Optional[str] = None

class SignalMetadata(BaseModel):
    frequency_mhz: float
    power_dbm: float
    modulation: str
    duration_ms: int
    region: str
    time_of_day: str
    repeat_count: int = 1
    known_pattern: Optional[str] = None

class GeoObservation(BaseModel):
    text: str
    context: str
    task_id: int
    case_id: str
    available_actions: List[str]
    step: int = 0
    difficulty: str = "easy"
    signal_metadata: Optional[SignalMetadata] = None
    signal_history: Optional[List[str]] = None
    threat_indicators: Optional[List[str]] = None

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
    total_score: float = 0.0
    difficulty: str = "easy"
