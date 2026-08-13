from pathlib import Path

from app.core.company_manager import CompanyManager


class PromptManager:
    """
    Builds Emma's system prompt using company information
    and business-specific instructions.
    """

    def __init__(self, company_data: dict | None = None):
        self.prompt_path = Path("app/prompts/system_prompt.md")
        self.company_manager = CompanyManager(company_data)

    def get_system_prompt(self) -> str:

        prompt = self.prompt_path.read_text(
            encoding="utf-8"
        )

        company = self.company_manager.get_company()

        for key, value in company.items():

            if isinstance(value, list):

                value = "\n".join(
                    f"- {item}"
                    for item in value
                )

            prompt = prompt.replace(
                f"{{{{{key}}}}}",
                str(value)
            )

        return prompt