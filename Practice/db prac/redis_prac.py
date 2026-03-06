import asyncio

import redis.asyncio as redis


async def main():
    redis_client = redis.from_url("redis://localhost")
    await redis_client.set("my-key", "value")
    value = await redis_client.get("my-key")
    print(value)


if __name__ == "__main__":
    asyncio.run(main())
