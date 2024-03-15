import asyncio
import datetime as dt
import logging
from pathlib import Path
from typing import Self

import aiosqlite


logger = logging.getLogger(__name__)


TABLE_NAME = "cache"
KEY_COL = "key"
VAL_COL = "val"
CACHED_COL = "cached"
DATE_FMT = "%Y-%m-%d"


CREATE_TABLE = f"""
CREATE TABLE {TABLE_NAME} (
    {CACHED_COL} TEXT,
    {KEY_COL} TEXT,
    {VAL_COL} TEXT
);
""".strip()

GET_KEY = f"""
SELECT * FROM {TABLE_NAME} WHERE {KEY_COL} = "{{key}}"
""".strip()


ADD_KEY = f"""
INSERT INTO {TABLE_NAME} ({CACHED_COL}, {KEY_COL}, {VAL_COL})
VALUES ("{{cached}}", "{{key}}", "{{value}}");
""".strip()


async def create_cache(uri: str | Path) -> None:
    logger.info("Creating cache: %s", uri)
    async with aiosqlite.connect(uri) as db:
        await db.execute(CREATE_TABLE)
        await db.commit()


class Cache:
    @classmethod
    async def new(cls, uri: str | Path = ".py-cache") -> Self:
        cache = cls(uri=uri)
        if not cache.uri.exists():
            await create_cache(cache.uri)
        return cache

    def __init__(self, uri: str | Path) -> None:
        self.uri = Path(uri)

    async def get(self, key: str) -> str | None:
        logger.debug("Get %s", key)
        stmt = GET_KEY.format(key=key)
        logger.debug(stmt)
        async with aiosqlite.connect(self.uri) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(stmt) as cursor:
                row = await cursor.fetchone()
                logger.debug("Row: %r", row)
                if row:
                    return row[VAL_COL]

    async def add(self, key: str, value: str, cached: str | None = None) -> None:
        logger.debug("Add %s %s", key, value)
        cached = dt.datetime.utcnow().strftime(DATE_FMT) if cached is None else cached
        stmt = ADD_KEY.format(key=key, value=value, cached=cached)
        logger.debug(stmt)
        async with aiosqlite.connect(self.uri) as db:
            try:
                await db.execute(stmt)
            except Exception as e:
                logger.error("%r", e)
            else:
                await db.commit()
            finally:
                await db.rollback()
