"""Private HTTP interface for the Defensive Genius recommendation engine."""

import math
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from brain import DECK, recommend_defense


Lane = Literal["left", "right", "center"]


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enemy_cards: list[str] = Field(min_length=1, max_length=30)
    elixir: StrictInt = Field(ge=0, le=10)
    hand: list[str] | None = Field(default=None, max_length=8)
    lanes: dict[str, Lane] | None = None
    times_to_tower: dict[str, float] | None = None

    @field_validator("enemy_cards")
    @classmethod
    def validate_enemy_cards(cls, cards):
        normalized = [card.strip() for card in cards]
        if any(not card for card in normalized):
            raise ValueError("enemy_cards entries must not be blank.")
        return normalized

    @field_validator("hand")
    @classmethod
    def validate_hand(cls, cards):
        if cards is None:
            return None
        normalized = [card.strip() for card in cards]
        if any(not card for card in normalized):
            raise ValueError("hand entries must not be blank.")
        unknown = [card for card in normalized if card not in DECK]
        if unknown:
            raise ValueError(
                "hand contains cards outside the configured deck: "
                + ", ".join(unknown)
            )
        return normalized

    @field_validator("times_to_tower")
    @classmethod
    def validate_times_to_tower(cls, values):
        if values is None:
            return None
        for card, seconds in values.items():
            if not math.isfinite(seconds) or not 0 <= seconds <= 120:
                raise ValueError(
                    f"Time for {card!r} must be a finite number from 0 to 120 seconds."
                )
        return values

    @model_validator(mode="after")
    def validate_battlefield_keys(self):
        enemy_names = {card.casefold() for card in self.enemy_cards}
        for field_name in ("lanes", "times_to_tower"):
            values = getattr(self, field_name) or {}
            unrelated = [
                card for card in values if card.strip().casefold() not in enemy_names
            ]
            if unrelated:
                raise ValueError(
                    f"{field_name} keys must name enemy_cards; "
                    f"not found: {', '.join(unrelated)}."
                )
        return self


class CardRecommendation(BaseModel):
    card: str
    cost: int
    job: str
    threats: list[str]
    placement: str | None
    timing: str | None


class ThreatOutcome(BaseModel):
    card: str
    coverage: float
    status: str
    seconds_to_tower: float | None
    lane: str | None
    contributed_by: list[str]


class AnalyzeResponse(BaseModel):
    recommended_cards: list[CardRecommendation]
    total_cost: int
    remaining_elixir: float
    threats: list[ThreatOutcome]
    confidence: str
    limitations: list[str]
    explanation: str


class HealthResponse(BaseModel):
    status: Literal["ok"]


app = FastAPI(
    title="Defensive Genius API",
    description="Local API for the private Defensive Genius Clash Royale companion.",
    version="0.1.0",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in ("body",)]
        details.append(
            {
                "field": ".".join(location) or "request",
                "message": error["msg"],
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request did not pass validation.",
            "details": details,
        },
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    lanes = {
        card.casefold(): lane
        for card, lane in (request.lanes or {}).items()
    }
    times = {
        card.casefold(): seconds
        for card, seconds in (request.times_to_tower or {}).items()
    }
    enemy_state = [
        {
            "card": card,
            "lane": lanes.get(card.casefold()),
            "seconds_to_tower": times.get(card.casefold()),
        }
        for card in request.enemy_cards
    ]

    plan = recommend_defense(enemy_state, request.elixir, request.hand)
    if plan["cards"]:
        explanation = " ".join(
            f"{action['card']}: {action['job']}"
            for action in plan["cards"]
        )
    else:
        explanation = plan["reason"] or "No defensive recommendation is available."

    return {
        "recommended_cards": plan["cards"],
        "total_cost": plan["total_cost"],
        "remaining_elixir": plan["remaining_elixir"],
        "threats": plan["threats"],
        "confidence": plan["confidence"],
        "limitations": plan["limitations"],
        "explanation": explanation,
    }
