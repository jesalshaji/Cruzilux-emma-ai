import asyncio

from app.ai.live_session import LiveSession


async def main():
    live = LiveSession()

    async with await live.connect() as session:
        print("✅ Live session connected!")


if __name__ == "__main__":
    asyncio.run(main())