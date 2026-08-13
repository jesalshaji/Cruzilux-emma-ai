from datetime import datetime
from zoneinfo import ZoneInfo


class RuntimeContext:
    """
    Provides current date and time information
    using the current company's timezone.
    """

    def __init__(self, timezone: str):
        self.timezone = timezone

    def get_context(self) -> dict:
        now = datetime.now(
            ZoneInfo(self.timezone)
        )

        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "current_day": now.strftime("%A"),
            "timezone": self.timezone,
        }