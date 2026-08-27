from email.policy import default
from enum import StrEnum
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
from typing import Optional


class Environment(StrEnum):
    """Application environment types.

    Defines the possible environments the application can run in:
    development, staging, production, and test.

    Attributes:
        DEVELOPMENT (str): The development environment.
        STAGING (str): The staging environment.
        PRODUCTION (str): The production environment.
        TEST (str): The test environment.
    """

    DEVELOPMENT = "development" # Local DB, debug logs, mock services
    STAGING = "staging" # Staging DB/API, production-like setup
    PRODUCTION = "production" # Real DB, real APIs, strict settings
    TEST = "test" # Temporary DB, mocked APIs


class LogLevel(StrEnum):
    """Log level types.

    Defines the possible log levels for the application.

    Attributes:
        DEBUG(str): Debug log level.
        INFO (str): Info log level.
        WARNING (str): Warning log level.
        ERROR (str): Error log level.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogRenderer(StrEnum):
    """Log renderer types.

    Defines the possible log renderers for the application.

    Attributes:
        CONSOLE (str): Console log renderer.
        JSON (str): JSON log renderer.
    """
    CONSOLE = "console"
    JSON = "json"


def get_enviroment() -> Environment:
    """Get the current environment.

    Must be set via export APP_ENV=development | staging| production| test.
    it will be used to load the appropriate .env file only.

    Returns:
        Environment: The current environment (development, staging, production, or test)"""
    match os.getenv("APP_ENV", "development").lower():
        case "production" | "prod":
            return Environment.PRODUCTION
        case "staging" | "stage":
            return Environment.STAGING
        case "test" | "testing":
            return Environment.TEST
        case _:
            return Environment.DEVELOPMENT


def load_env_file() -> str | Path | None:
    """load enviroment .env file"""
    env = get_enviroment()
    print(f"Loading enviroment: {env}")

    base_dir = Path(__file__).parents[2]

    # define env files in priority order
    env_files = [Path(base_dir, f".env.{env.value}"), Path(base_dir, ".env")]

    # load the first env file exists
    for env_file in env_files:
        if env_file.is_file():
            load_dotenv(env_file)
            print(f"loaded enviroment from {env_file}")
            return env_file

    return None


ENV_FILE = load_env_file()

ENV_DEFAULTS = {
    Environment.DEVELOPMENT: {
        "DEBUG": True,
        "LOG_LEVEL": LogLevel.DEBUG,
        "LOG_RENDERER": LogRenderer.CONSOLE
    },

    Environment.STAGING: {
        "DEBUG": False,
        "LOG_LEVEL": LogLevel.INFO,
        "LOG_RENDERER": LogRenderer.JSON
    },

    Environment.PRODUCTION: {
        "DEBUG": False,
        "LOG_LEVEL": LogLevel.WARNING,
        "LOG_RENDERER": LogRenderer.JSON
    },

    Environment.TEST: {
        "DEBUG": True,
        "LOG_LEVEL": LogLevel.DEBUG,
        "LOG_RENDERER": LogRenderer.CONSOLE
    }
}


class Settings(BaseSettings):
    """Application settings configuration.

    Manages application configuration with support for environment-specific
    settings and validation of environment aliases.
    
    load_dotenv() and SettingsConfigDict(env_file=...) can both read the .env file, but they serve different purposes.

    Think of it like this:
    load_dotenv() -> puts values into os.environ -> os.getenv("PROJECT_NAME")
    while: SettingsConfigDict(env_file=...) -> tells Pydantic where to get Settings values -> Settings() -> settings.PROJECT_NAME
    """

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    # ===================================================================
    # Application Settings
    # ===================================================================
    APP_ENV: Environment = Field(...)
    PROJECT_NAME: str = Field(..., max_length=100)
    VERSION: str = Field(...)
    PROJECT_ROOT: str = Field(...)
    LOG_LEVEL: Optional[str] = Field(default=None)

    # ===================================================================
    # Logging Settings
    # ===================================================================
    DEBUG: Optional[bool] = Field(default=None)
    LOG_LEVEL: Optional[LogLevel] = Field(default=None)
    LOG_RENDERER: Optional[LogRenderer] = Field(default=None)
    LOG_DIR: Optional[str] = Field(default='storage/logs')
    LOG_MAX_BYTES: Optional[int] = Field(default= 10 * 1024 * 1024)
    LOG_BACKUP_COUNT: Optional[int] = Field(default=10)


    @model_validator(mode="after")
    def configure_environment_defaults(self):
        """After Pydantic has loaded and validated my settings, 
        fill in any missing settings with defaults appropriate for the current environment.

        if getattr(self, key, None) is None:
        This asks: Does the Settings object already have a value for this setting?
        For example: self.DEBUG = None
        Then: getattr(self, "DEBUG", None)
        returns: None
        Therefore: None is None is True.
        So it sets the default.
        Then this setattr(self, key, value)
        means: Set this attribute on the Settings object.
        For example:
        key = "DEBUG"
        value = False
        becomes effectively: self.DEBUG = False

        Returns:
            Settings: The settings instance with environment defaults applied.
        """
        current_env_defaults = ENV_DEFAULTS.get(self.APP_ENV, {})

        for key, value in current_env_defaults.items():
            if getattr(self, key, None) is None: # Does the Settings object already have a value for this setting? self.DEBUG = None
                setattr(self, key, value)

        return self

    @field_validator("APP_ENV", mode="before") # apply before pydantic validation
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        """Normalize APP_ENV aliases to supported environment values

        Args:
            value: The input environment value to normalize.

        Returns:
            str: The normalized environment value.
        """
        aliases = {
            "dev": "development",
            "development": "development",
            "stage": "staging",
            "staging": "staging",
            "prod": "production",
            "production": "production",
            "test": "test",
            "testing": "test"
        }

        normalized_env = aliases.get(str(value).lower())
        if normalized_env is None:
            raise ValueError(
                f"Invalid APP_ENV '{value}'"
                f"Expected one of: {','.join(sorted(aliases.keys()))}"
            )
        return normalized_env


settings = Settings()

def main():
    print(f"welcome from `{os.path.basename(__file__).split('.')[0]}` modeul, nothing to do ^___^!")
    for key, value in settings.model_dump().items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

