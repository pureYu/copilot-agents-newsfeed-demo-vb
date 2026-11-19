from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.articles import router as articles_router
from app.api.ingest import router as ingest_router
from app.api.sources import router as sources_router
from app.core.logging import configure_logging
from app.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await create_tables()
    yield


app = FastAPI(
    title="Newsfeed API",
    version="0.1.0",
    description="News reader backend — sources, ingestion, and article retrieval.",
    lifespan=lifespan,
)

app.include_router(sources_router)
app.include_router(articles_router)
app.include_router(ingest_router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
