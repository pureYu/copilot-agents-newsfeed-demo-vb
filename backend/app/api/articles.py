from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Article
from app.schemas.articles import ArticleListResponse, ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    source_id: int | None = None,
    search: str | None = Query(default=None, max_length=200),
    tag: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ArticleListResponse:
    query = select(Article).options(selectinload(Article.source))
    count_q = select(func.count(Article.id)).select_from(Article)

    if source_id is not None:
        query = query.where(Article.source_id == source_id)
        count_q = count_q.where(Article.source_id == source_id)

    if search:
        search_filter = or_(
            Article.title.ilike(f"%{search}%"),
            Article.summary.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_q = count_q.where(search_filter)

    if tag:
        tags_each = func.json_each(Article.tags).table_valued("value")
        tag_filter = (
            select(literal(1))
            .select_from(tags_each)
            .where(tags_each.c.value == tag)
            .correlate(Article)
            .exists()
        )
        query = query.where(tag_filter)
        count_q = count_q.where(tag_filter)

    total = (await session.execute(count_q)).scalar_one()
    result = await session.execute(
        query.order_by(Article.ingested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    articles = list(result.scalars().all())

    return ArticleListResponse(
        items=articles,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    session: AsyncSession = Depends(get_session),
) -> Article:
    result = await session.execute(
        select(Article)
        .options(selectinload(Article.source))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found.")
    return article
