from pathlib import Path


class PromptManager:
    def __init__(self):
        self.prompt_path = Path("app/prompts/system_prompt.md")

    def get_system_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")