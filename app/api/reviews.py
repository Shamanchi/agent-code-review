"""Эндпоинты ревью, фидбека и весов правил."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.evolution import EvolutionStore, get_store
from app.services.reviewer import ReviewResult, review_code

router = APIRouter()


class ReviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200_000)
    language: str = "python"


class FeedbackRequest(BaseModel):
    rule: str = Field(min_length=1, max_length=64)
    accepted: bool


def get_evolution_store(settings: Settings = Depends(get_settings)) -> EvolutionStore:
    return get_store(
        min_weight=settings.min_weight,
        max_weight=settings.max_weight,
        upvote_step=settings.upvote_step,
        downvote_step=settings.downvote_step,
    )


@router.post("/reviews", response_model=ReviewResult)
async def create_review(
    request: ReviewRequest,
    settings: Settings = Depends(get_settings),
    store: EvolutionStore = Depends(get_evolution_store),
) -> ReviewResult:
    if request.language.lower() != "python":
        raise HTTPException(status_code=422, detail="Only python is supported in v0.1.0")
    return review_code(request.code, store, max_function_lines=settings.max_function_lines)


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    store: EvolutionStore = Depends(get_evolution_store),
) -> dict:
    weight = store.feedback(request.rule, request.accepted)
    return {"rule": request.rule, "accepted": request.accepted, "weight": weight}


@router.get("/rules")
async def list_rules(store: EvolutionStore = Depends(get_evolution_store)) -> dict:
    return {"weights": store.weights()}
