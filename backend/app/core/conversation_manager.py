from app.ai.live_session import LiveSession


class ConversationManager:
    """
    Manages a single conversation between one customer and Emma.
    """

    def __init__(self):
        self.live_session = LiveSession()
        self.session = None

    async def start(self):
        """
        Start a new Gemini Live session.
        """
        self.session = await self.live_session.connect()

    async def stop(self):
        """
        Close the current Gemini Live session.
        """
        if self.session:
            await self.session.close()
            self.session = None