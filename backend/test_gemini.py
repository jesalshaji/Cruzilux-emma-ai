from pathlib import Path

from app.ai.gemini_service import GeminiService

system_prompt = Path(
    "app/prompts/system_prompt.md"
).read_text(encoding="utf-8")

gemini = GeminiService()

reply = gemini.chat(
    system_prompt,
    "Hello!"
)

print(reply)