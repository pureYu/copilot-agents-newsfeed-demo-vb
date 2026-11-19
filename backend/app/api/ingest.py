import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Source, SourceType
from app.schemas.ingest import IngestionRunResponse
from app.services import rss, scrape

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = structlog.get_logger(__name__)


async def _dispatch_ingest(session: AsyncSession, source: Source):
    """Route ingestion to the correct service based on source_type."""
    if source.source_type == SourceType.scrape:
        return await scrape.ingest_source(session, source)
    return await rss.ingest_source(session, source)


@router.post("/{source_id}", response_model=IngestionRunResponse)
async def ingest_single(
    source_id: int,
    session: AsyncSession = Depends(get_session),
) -> IngestionRunResponse:
    """Trigger ingestion for a single source. Works regardless of enabled flag."""
    source = await session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    logger.info(
        "api.ingest.trigger",
        source_id=source_id,
        source_name=source.name,
        source_type=source.source_type,
    )
    run = await _dispatch_ingest(session, source)
    return run


@router.post("", response_model=list[IngestionRunResponse])
async def ingest_all(
    session: AsyncSession = Depends(get_session),
) -> list[IngestionRunResponse]:
    """Trigger ingestion for every enabled source sequentially."""
    result = await session.execute(
        select(Source).where(Source.enabled.is_(True))
    )
    sources = list(result.scalars().all())
    logger.info("api.ingest.bulk_trigger", source_count=len(sources))
    runs = []
    for source in sources:
        try:
            run = await _dispatch_ingest(session, source)
            runs.append(run)
        except Exception as exc:
            # Ensure the session is clean before continuing to the next source.
            try:
                await session.rollback()
            except Exception:
                pass
            logger.error(
                "api.ingest.source_failed",
                source_id=source.id,
                source_name=source.name,
                error=str(exc),
                exc_info=True,
            )
    return runs
