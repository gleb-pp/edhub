from pydantic_settings import BaseSettings, SettingsConfigDict


class MaterialSettings(BaseSettings):
    """Material info settings."""

    name_min_length: int = 3
    name_max_length: int = 80
    description_min_length: int = 3
    description_max_length: int = 10000

    model_config = SettingsConfigDict(env_prefix="material_")


material_settings = MaterialSettings()
