from datetime import timedelta

from pydantic import Base64Str
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    private_key: Base64Str
    application_id: int = 798085
    installation_id: int = 46187215
    organization_id: str = "hakasecurity"
    environment: str = "development"
    github_scrape_interval: int = timedelta(seconds=120).seconds


settings = Settings()  # type: ignore
