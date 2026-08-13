import json
from pathlib import Path


class CompanyManager:
    """
    Loads and provides the active company's configuration.
    """

    def __init__(self, company_data: dict | None = None):
        self.company_path = Path("app/config/company.json")

        if company_data is not None:
            self.company = company_data
        else:
            self.company = self._load_company()

    def _load_company(self) -> dict:
        with open(
            self.company_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def get_company(self) -> dict:
        return self.company