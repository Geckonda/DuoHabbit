"""Chat models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from duohabit.db import Base
from duohabit.models.mixins import TimestampMixin

# pylint: disable=too-few-public-methods
# Models exist for a different reason.


class Conversation(TimestampMixin, Base):
    """A conversation between users. Currently always a pair, groups fit as-is."""

    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Денормализация: без нее список диалогов пришлось бы сортировать
    # джойном по всей таблице сообщений
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    # Новый диалог начинается pending - собеседник может читать, но не отвечать,
    # пока не примет (см. services/chat.py: accept_conversation/decline_conversation)
    status: Mapped[str] = mapped_column(String(20), default="accepted", nullable=False)
    initiator_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )

    participants: Mapped[list["ConversationParticipant"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class ConversationParticipant(TimestampMixin, Base):
    """Membership of a user in a conversation, with their read position."""

    __tablename__ = "conversation_participant"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True
    )

    # Не FK: сообщения не удаляются, а лишняя ссылочная зависимость тут не нужна
    last_read_message_id: Mapped[int | None] = mapped_column(Integer)

    conversation: Mapped["Conversation"] = relationship(back_populates="participants")

    __table_args__ = (
        UniqueConstraint(
            "conversation_id", "user_id", name="uq_conversation_participant"
        ),
    )


class Message(TimestampMixin, Base):
    """A single chat message."""

    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE")
    )
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(4000), nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    # История листается курсором по id, индекс покрывает выборку внутри диалога
    __table_args__ = (Index("ix_message_conversation_id_id", "conversation_id", "id"),)
