from datetime import timedelta

from pydantic import Base64Str
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    github_scrape_interval: int = timedelta(seconds=120).seconds
    port: int = 12345

    private_key: Base64Str
    application_id: int
    installation_id: int
    organization_id: str


settings = Settings()  # type: ignore
