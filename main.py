import asyncio
import logging
import os


from py_cache.cache import Cache


async def main() -> None:
    c = await Cache.new()
    no_val = await c.get("x")
    assert not no_val
    await c.add("x", "y")
    val = await c.get("x")
    assert val == "y", val


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(main())
