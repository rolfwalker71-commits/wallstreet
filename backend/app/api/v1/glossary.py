from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import GlossaryTerm
from app.schemas.common import GlossaryTermOut

router = APIRouter()


@router.get("", response_model=list[GlossaryTermOut])
async def list_terms(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[GlossaryTermOut]:
    stmt = select(GlossaryTerm).order_by(GlossaryTerm.term)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(GlossaryTerm.term.ilike(like), GlossaryTerm.short_definition.ilike(like))
        )
    rows = (await db.execute(stmt)).scalars().all()
    return [GlossaryTermOut.model_validate(r) for r in rows]


@router.get("/{slug}", response_model=GlossaryTermOut)
async def get_term(slug: str, db: AsyncSession = Depends(get_db)) -> GlossaryTermOut:
    row = (
        await db.execute(select(GlossaryTerm).where(GlossaryTerm.slug == slug))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Begriff nicht gefunden")
    return GlossaryTermOut.model_validate(row)