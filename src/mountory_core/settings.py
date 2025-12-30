import warnings
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


def check_default_secret(
    var_name: str, value: str | None, env: str | None = None
) -> None:
    if value == "changethis":
        message = (
            f'The value of {var_name} is "changethis", '
            "for security, please change it, at least for deployments."
        )
        if env == "local":
            warnings.warn(message, stacklevel=1)
        else:
            raise ValueError(message)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        extra="ignore",
    )
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        return check_default_secret(var_name, value, self.ENVIRONMENT)
