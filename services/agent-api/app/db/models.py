"""Conversation storage. Messages hold mentor text, never API tokens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column()


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_position", "conversation_id", "position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column()
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text())
    tool_trace: Mapped[str] = mapped_column(Text(), default="[]")
    created_at: Mapped[datetime] = mapped_column()
