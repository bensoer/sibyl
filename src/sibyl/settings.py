from dataclasses import dataclass
from enum import Enum
from os import environ
from typing import Literal

from pydantic_settings import BaseSettings
from typing_extensions import Self

from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
    model_validator
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    HEALTH_CHECK_PORT: int = Field(ge=1024, lt=65535, default=8080, description="Port the Health Check Endpoints Are Served Over")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO"

    SLACK_BOT_TOKEN: str = Field(description="Slack Bot Token for sending notifications")
    SLACK_CHANNEL: str = Field(description="Slack Channel ID to send notifications to")