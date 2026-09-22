import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_event
from ..matching import find_matching
from ..models import Constraint, Event, Participant, utcnow
from ..schemas import (
    ConstraintCreate,
    ConstraintOut,
    DrawResponse,
    EventCreate,
    EventCreated,
    ParticipantCreate,
    ParticipantOut,
)
from ..serialize import serialize_detail, serialize_event_created

router = APIRouter(prefix="/api/events", tags=["events"])


def _new_token() -> str:
    return secrets.token_urlsafe(24)


@router.post("", response_model=EventCreated, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(title=payload.title.strip(), edit_token=_new_token())
    db.add(event)
    db.commit()
    db.refresh(event)
    return serialize_event_created(event)


@router.get("/{event_id}")
def get_event(event: Event = Depends(require_event)):
    return serialize_detail(event)


@router.post(
    "/{event_id}/participants",
    response_model=ParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
def add_participant(
    payload: ParticipantCreate,
    event: Event = Depends(require_event),
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="姓名不能为空")
    if event.drawn:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动已抽签，不能再修改参与者")
    if any(p.name == name for p in event.participants):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已存在同名参与者")

    participant = Participant(event_id=event.id, name=name, reveal_token=_new_token())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return ParticipantOut(
        id=participant.id,
        name=participant.name,
        revealed=participant.revealed,
        revealed_at=participant.revealed_at,
    )


@router.delete("/{event_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    participant_id: int,
    event: Event = Depends(require_event),
    db: Session = Depends(get_db),
):
    if event.drawn:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动已抽签，不能再修改参与者")
    participant = db.get(Participant, participant_id)
    if participant is None or participant.event_id != event.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="参与者不存在")

    # 先移除引用到该参与者的禁配关系，再删除参与者
    db.query(Constraint).filter(
        Constraint.event_id == event.id,
        (Constraint.giver_id == participant_id) | (Constraint.receiver_id == participant_id),
    ).delete(synchronize_session=False)
    db.delete(participant)
    db.commit()
    return None


@router.post(
    "/{event_id}/constraints",
    response_model=ConstraintOut,
    status_code=status.HTTP_201_CREATED,
)
def add_constraint(
    payload: ConstraintCreate,
    event: Event = Depends(require_event),
    db: Session = Depends(get_db),
):
    if event.drawn:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动已抽签，不能再修改禁配关系")
    if payload.giver_id == payload.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="禁配关系必须指向两位不同的参与者（不能抽到自己是系统默认保证的）",
        )

    participant_ids = {p.id for p in event.participants}
    if payload.giver_id not in participant_ids or payload.receiver_id not in participant_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="参与者不存在")

    exists = db.query(Constraint).filter_by(
        event_id=event.id, giver_id=payload.giver_id, receiver_id=payload.receiver_id
    ).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该禁配关系已存在")

    constraint = Constraint(
        event_id=event.id, giver_id=payload.giver_id, receiver_id=payload.receiver_id
    )
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return ConstraintOut(
        id=constraint.id, giver_id=constraint.giver_id, receiver_id=constraint.receiver_id
    )


@router.delete("/{event_id}/constraints/{constraint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_constraint(
    constraint_id: int,
    event: Event = Depends(require_event),
    db: Session = Depends(get_db),
):
    if event.drawn:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动已抽签，不能再修改禁配关系")
    constraint = db.get(Constraint, constraint_id)
    if constraint is None or constraint.event_id != event.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="禁配关系不存在")
    db.delete(constraint)
    db.commit()
    return None


@router.post("/{event_id}/draw", response_model=DrawResponse)
def draw_event(event: Event = Depends(require_event), db: Session = Depends(get_db)):
    # 原子占位：把 drawn 从 0 更新为 1，并发请求中只有一个能成功
    updated = (
        db.query(Event)
        .filter(Event.id == event.id, Event.drawn.is_(False))
        .update({Event.drawn: True}, synchronize_session=False)
    )
    if updated == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动已经完成抽签")

    participants = db.query(Participant).filter(Participant.event_id == event.id).all()
    if len(participants) < 2:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="至少需要 2 位参与者才能抽签",
        )

    forbidden: set[tuple[int, int]] = {
        (c.giver_id, c.receiver_id)
        for c in db.query(Constraint).filter(Constraint.event_id == event.id).all()
    }

    match = find_matching([p.id for p in participants], forbidden)
    if match is None:
        # 无解：回滚占位标记，不写入任何配对，组织者调整后可重试
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="在当前禁配关系下不存在合法抽签方案，请放宽部分限制后重试（不会产生任何部分结果）",
        )

    # 用 Core 批量更新写 recipient_id：配对结果不使用 ORM relationship
    for giver_id, receiver_id in match.items():
        db.execute(
            sa_update(Participant)
            .where(Participant.id == giver_id)
            .values(recipient_id=receiver_id)
        )
    db.commit()

    return DrawResponse(drawn=True, participant_count=len(participants))
