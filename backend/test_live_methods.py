import asyncio

from app.ai.live_session import LiveSession


async def main():
    live = LiveSession()

    async with live.connect() as session:
        print(type(session))
        print(dir(session))


asyncio.run(main())