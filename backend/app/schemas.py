from datetime import datetime
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(default="秘密赠礼", min_length=1, max_length=120)


class EventOut(BaseModel):
    id: int
    title: str
    drawn: bool
    created_at: datetime


class EventCreated(EventOut):
    edit_token: str


class ParticipantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ParticipantOut(BaseModel):
    id: int
    name: str
    revealed: bool
    revealed_at: datetime | None = None


class ParticipantLinkOut(ParticipantOut):
    reveal_token: str


class ConstraintCreate(BaseModel):
    giver_id: int
    receiver_id: int


class ConstraintOut(BaseModel):
    id: int
    giver_id: int
    receiver_id: int


class EventDetail(EventOut):
    participants: list[ParticipantLinkOut]
    constraints: list[ConstraintOut]


class DrawResponse(BaseModel):
    drawn: bool
    participant_count: int


class RevealOut(BaseModel):
    name: str
    event_title: str
    drawn: bool
    revealed: bool
    recipient_name: str | None = None
    revealed_at: datetime | None = None
