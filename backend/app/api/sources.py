from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Source
from app.schemas.sources import (
    SourceCreate,
    SourceListResponse,
    SourceResponse,
    SourceUpdate,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(
    body: SourceCreate,
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = Source(
        name=body.name,
        url=str(body.url),
        source_type=body.source_type,
        config=body.config,
        enabled=body.enabled,
    )
    session.add(source)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="A source with this URL already exists.")
    await session.refresh(source)
    return source


@router.get("", response_model=SourceListResponse)
async def list_sources(
    enabled: bool | None = None,
    session: AsyncSession = Depends(get_session),
) -> SourceListResponse:
    query = select(Source)
    if enabled is not None:
        query = query.where(Source.enabled == enabled)
    result = await session.execute(query)
    sources = list(result.scalars().all())
    return SourceListResponse(items=sources, total=len(sources))


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    body: SourceUpdate,
    session: AsyncSession = Depends(get_session),
) -> Source:
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    await session.commit()
    await session.refresh(source)
    return source
