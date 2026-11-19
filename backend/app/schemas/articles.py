from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import SourceType


class SourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: SourceType


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    source: SourceSummary
    title: str
    url: str
    canonical_url: str | None
    author: str | None
    published_at: datetime | None
    summary: str | None
    content: str | None
    image_url: str | None
    tags: list
    ingested_at: datetime


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
