"""Repository-layer tests for MessageRepository (foundation for M5 chat persistence)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.constants import MessageRole, SafetySeverity
from app.db.repositories.message_repo import MessageRepository

from tests.fakes.fake_supabase import FakeSupabase


def _seed_message(
    fake_db: FakeSupabase,
    *,
    session_id: str,
    role: MessageRole = MessageRole.USER,
    content: str = "hello",
    created_at: datetime | None = None,
) -> str:
    """Insert a chat_messages row directly into the fake store."""
    message_id = str(uuid4())
    fake_db.seed(
        "chat_messages",
        [
            {
                "id": message_id,
                "session_id": session_id,
                "role": role.value,
                "content": content,
                "safety_flag": False,
                "safety_severity": SafetySeverity.NONE.value,
                "trace_id": None,
                "created_at": (created_at or datetime.now(UTC)).isoformat(),
            },
        ],
    )
    return message_id


@pytest.mark.asyncio
async def test_create_returns_message_response(
    message_repo: MessageRepository,
) -> None:
    """``create`` inserts a row and returns a typed MessageResponse with timestamps."""
    session_id = str(uuid4())

    message = await message_repo.create(
        {
            "session_id": session_id,
            "role": MessageRole.USER.value,
            "content": "hi",
        },
    )

    assert message.session_id == session_id
    assert message.role == MessageRole.USER
    assert message.content == "hi"
    assert message.safety_flag is False
    assert message.safety_severity == SafetySeverity.NONE
    assert message.created_at is not None


@pytest.mark.asyncio
async def test_list_for_session_returns_oldest_first(
    message_repo: MessageRepository,
    fake_db: FakeSupabase,
) -> None:
    """``list_for_session`` orders messages by created_at ascending by default."""
    session_id = str(uuid4())
    other_session_id = str(uuid4())
    base_time = datetime(2030, 1, 1, tzinfo=UTC)
    _seed_message(
        fake_db,
        session_id=session_id,
        content="second",
        created_at=base_time + timedelta(seconds=10),
    )
    _seed_message(
        fake_db,
        session_id=session_id,
        content="first",
        created_at=base_time,
    )
    _seed_message(
        fake_db,
        session_id=other_session_id,
        content="other-session",
    )

    messages = await message_repo.list_for_session(session_id=session_id)

    assert [m.content for m in messages] == ["first", "second"]


@pytest.mark.asyncio
async def test_list_for_session_respects_limit_and_offset(
    message_repo: MessageRepository,
    fake_db: FakeSupabase,
) -> None:
    """``list_for_session`` honours ``limit`` and ``offset`` for pagination."""
    session_id = str(uuid4())
    base_time = datetime(2030, 1, 1, tzinfo=UTC)
    for i in range(5):
        _seed_message(
            fake_db,
            session_id=session_id,
            content=f"msg-{i}",
            created_at=base_time + timedelta(seconds=i),
        )

    page = await message_repo.list_for_session(
        session_id=session_id,
        limit=2,
        offset=1,
    )

    assert [m.content for m in page] == ["msg-1", "msg-2"]
