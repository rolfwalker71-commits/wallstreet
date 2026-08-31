from __future__ import annotations

import threading
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import LlmUsage

_lock = threading.Lock()
_current: list[dict] | None = None


@contextmanager
def usage_scope():
    global _current
    bucket: list[dict] = []
    with _lock:
        _current = bucket
    try:
        yield bucket
    finally:
        with _lock:
            if _current is bucket:
                _current = None


def record_usage(purpose: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    with _lock:
        if _current is None:
            return
        _current.append(
        {
            "purpose": purpose,
            "model": model,
            "prompt_tokens": int(prompt_tokens or 0),
            "completion_tokens": int(completion_tokens or 0),
        }
    )


def usage_from_message(msg) -> tuple[int, int]:
    meta = getattr(msg, "usage_metadata", None) or {}
    if meta:
        return int(meta.get("input_tokens") or 0), int(meta.get("output_tokens") or 0)
    raw = (getattr(msg, "response_metadata", None) or {}).get("token_usage") or {}
    return int(raw.get("prompt_tokens") or 0), int(raw.get("completion_tokens") or 0)


async def persist_usage(
    session: AsyncSession,
    rows: list[dict] | None,
    run_id: UUID | None = None,
) -> None:
    for row in rows or []:
        session.add(
            LlmUsage(
                model=row["model"],
                purpose=row["purpose"],
                prompt_tokens=row["prompt_tokens"],
                completion_tokens=row["completion_tokens"],
                run_id=run_id,
            )
        )
    await session.flush()


def _window_start(hours: int) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


async def usage_summary(session: AsyncSession) -> dict:
    async def _sum(since: datetime | None = None) -> dict:
        stmt = select(
            func.coalesce(func.sum(LlmUsage.prompt_tokens), 0),
            func.coalesce(func.sum(LlmUsage.completion_tokens), 0),
            func.count(LlmUsage.id),
        )
        if since is not None:
            stmt = stmt.where(LlmUsage.created_at >= since)
        prompt, completion, calls = (await session.execute(stmt)).one()
        return {
            "prompt_tokens": int(prompt),
            "completion_tokens": int(completion),
            "total_tokens": int(prompt) + int(completion),
            "calls": int(calls),
        }

    async def _by_model(since: datetime) -> list[dict]:
        stmt = (
            select(
                LlmUsage.model,
                func.coalesce(func.sum(LlmUsage.prompt_tokens), 0),
                func.coalesce(func.sum(LlmUsage.completion_tokens), 0),
                func.count(LlmUsage.id),
            )
            .where(LlmUsage.created_at >= since)
            .group_by(LlmUsage.model)
        )
        return [
            {
                "model": row[0],
                "prompt_tokens": int(row[1]),
                "completion_tokens": int(row[2]),
                "calls": int(row[3]),
            }
            for row in (await session.execute(stmt)).all()
        ]

    return {
        "today": await _sum(_window_start(24)),
        "month": await _sum(_window_start(24 * 30)),
        "all": await _sum(None),
        "models_today": await _by_model(_window_start(24)),
        "models_month": await _by_model(_window_start(24 * 30)),
    }
