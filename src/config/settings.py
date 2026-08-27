from email.mime import base
from enum import StrEnum
import os
from pathlib import Path
from dotenv import load_dotenv

class Enviroment(StrEnum):
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


def get_enviroment() -> Enviroment:
    """Get the current environment.

    Must be set via export APP_ENV=development | staging| production| test.
    it will be used to load the appropriate .env file only.

    Returns:
        Environment: The current environment (development, staging, production, or test)"""
    match os.getenv("APP_ENV", "development").lower():
        case "production" | "prod":
            return Enviroment.PRODUCTION
        case "staging" | "stage":
            return Enviroment.STAGING
        case "test" | "testing":
            return Enviroment.TEST
        case _:
            return Enviroment.DEVELOPMENT


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
