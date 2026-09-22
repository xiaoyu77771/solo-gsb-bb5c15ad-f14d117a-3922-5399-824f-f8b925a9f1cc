from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, aliased

from ..database import get_db
from ..models import Event, Participant, utcnow
from ..schemas import RevealOut

router = APIRouter(prefix="/api/reveal", tags=["reveal"])

Recipient = aliased(Participant)


def _load_participant(reveal_token: str, db: Session) -> tuple[Participant, str | None]:
    """按揭晓令牌取参与者，并通过显式 JOIN 读取收礼人姓名。

    不依赖 Participant.recipient 自引用关系的懒加载：直接用 SQL 的
    LEFT OUTER JOIN 保证拿到的就是数据库里当前的 recipient_id 对应行。
    """
    row = (
        db.query(Participant, Recipient.name)
        .outerjoin(Recipient, Recipient.id == Participant.recipient_id)
        .filter(Participant.reveal_token == reveal_token)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="揭晓链接无效")
    return row[0], row[1]


@router.get("/{reveal_token}", response_model=RevealOut)
def reveal_status(reveal_token: str, db: Session = Depends(get_db)):
    p, recipient_name = _load_participant(reveal_token, db)
    # 未抽签或已揭晓（或已揭晓后再次访问）都不返回具体结果
    shown = recipient_name if p.event.drawn and not p.revealed else None
    return RevealOut(
        name=p.name,
        event_title=p.event.title,
        drawn=p.event.drawn,
        revealed=p.revealed,
        recipient_name=shown,
        revealed_at=p.revealed_at,
    )


@router.post("/{reveal_token}", response_model=RevealOut)
def reveal_now(reveal_token: str, db: Session = Depends(get_db)):
    p, _ = _load_participant(reveal_token, db)

    if not p.event.drawn:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动尚未抽签")
    if p.revealed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该链接已经揭晓过，结果只能查看一次")

    # 原子条件更新：只有 revealed 仍为 False 时才能揭晓成功
    updated = (
        db.query(Participant)
        .filter(Participant.id == p.id, Participant.revealed.is_(False))
        .update({Participant.revealed: True, Participant.revealed_at: utcnow()},
                synchronize_session=False)
    )
    if updated == 0:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该链接已经揭晓过，结果只能查看一次")
    db.commit()

    # 提交后重新 JOIN 查询，避免使用更新前的快照
    p2, recipient_name = _load_participant(reveal_token, db)
    return RevealOut(
        name=p2.name,
        event_title=p2.event.title,
        drawn=True,
        revealed=True,
        recipient_name=recipient_name,
        revealed_at=p2.revealed_at,
    )
