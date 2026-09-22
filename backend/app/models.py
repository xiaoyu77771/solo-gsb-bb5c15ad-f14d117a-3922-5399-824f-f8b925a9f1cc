from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    edit_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    drawn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    participants: Mapped[list["Participant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    constraints: Mapped[list["Constraint"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    reveal_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    recipient_id: Mapped[int | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL"), nullable=True
    )
    revealed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped[Event] = relationship(back_populates="participants")
    # 注意：不为 recipient_id 建立自引用 relationship。配对结果一律用显式
    # JOIN 查询读取，避免同表自引用关系在 Identity Map 中的缓存歧义。


class Constraint(Base):
    __tablename__ = "constraints"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    giver_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))

    event: Mapped[Event] = relationship(back_populates="constraints")
