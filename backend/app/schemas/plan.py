from typing import List
from pydantic import BaseModel


class PlanResponse(BaseModel):
    name: str
    price: float
    max_accounts: int
    features: List[str]


class PlansListResponse(BaseModel):
    current_plan: str
    plans: List[PlanResponse]
