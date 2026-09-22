from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import Event


def require_event(
    event_id: int,
    x_event_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Event:
    """校验活动存在，且组织者请求携带了正确的 edit token。"""
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    if not x_event_token or x_event_token != event.edit_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="组织者令牌无效")
    return event
