from .models import Event, Participant, Constraint
from .schemas import (
    ConstraintOut,
    EventCreated,
    EventDetail,
    EventOut,
    ParticipantLinkOut,
)


def serialize_event(event: Event) -> EventOut:
    return EventOut(
        id=event.id,
        title=event.title,
        drawn=event.drawn,
        created_at=event.created_at,
    )


def serialize_event_created(event: Event) -> EventCreated:
    return EventCreated(
        id=event.id,
        title=event.title,
        drawn=event.drawn,
        created_at=event.created_at,
        edit_token=event.edit_token,
    )


def serialize_detail(event: Event) -> EventDetail:
    return EventDetail(
        id=event.id,
        title=event.title,
        drawn=event.drawn,
        created_at=event.created_at,
        participants=[
            ParticipantLinkOut(
                id=p.id,
                name=p.name,
                revealed=p.revealed,
                revealed_at=p.revealed_at,
                # 揭晓链接只在抽签完成后对组织者开放分发
                reveal_token=p.reveal_token if event.drawn else "",
            )
            for p in event.participants
        ],
        constraints=[
            ConstraintOut(id=c.id, giver_id=c.giver_id, receiver_id=c.receiver_id)
            for c in event.constraints
        ],
    )
