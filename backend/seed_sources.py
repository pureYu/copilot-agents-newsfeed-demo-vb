"""Seed script: insert a curated set of public RSS sources.

All sources are RSS feeds explicitly published for syndication — they are
compliant with the project requirement to respect robots.txt and publisher
terms of service.  No scrape sources are added here.

Usage (from the backend/ directory, with the virtualenv active):

    python seed_sources.py

The script is idempotent: it skips sources whose URL is already in the
database (unique constraint) and prints the outcome for each entry.
"""

import asyncio

from sqlalchemy import select

from app.database import create_tables, engine, AsyncSessionLocal
from app.models import Source, SourceType

# ---------------------------------------------------------------------------
# Curated public RSS feeds
# Each entry: (name, url, tags_hint)
# All are explicitly published syndication feeds — no scraping involved.
# ---------------------------------------------------------------------------
RSS_SOURCES: list[tuple[str, str]] = [
    (
        "BBC News – Top Stories",
        "https://feeds.bbci.co.uk/news/rss.xml",
    ),
    (
        "The Guardian – World",
        "https://www.theguardian.com/world/rss",
    ),
    (
        "NPR – News",
        "https://feeds.npr.org/1001/rss.xml",
    ),
    (
        "TechCrunch",
        "https://techcrunch.com/feed/",
    ),
    (
        "Ars Technica",
        "https://feeds.arstechnica.com/arstechnica/index",
    ),
]


async def seed() -> None:
    # Ensure tables exist (safe to call on an already-initialised DB).
    await create_tables()

    async with AsyncSessionLocal() as session:
        existing_urls: set[str] = set(
            row[0]
            for row in (await session.execute(select(Source.url))).all()
        )

        added = 0
        skipped = 0
        for name, url in RSS_SOURCES:
            if url in existing_urls:
                print(f"  SKIP  {name} — already present")
                skipped += 1
                continue

            source = Source(
                name=name,
                url=url,
                source_type=SourceType.rss,
                config={},
                enabled=True,
            )
            session.add(source)
            print(f"  ADD   {name}")
            added += 1

        await session.commit()

    await engine.dispose()
    print(f"\nDone: {added} added, {skipped} skipped.")


if __name__ == "__main__":
    asyncio.run(seed())
