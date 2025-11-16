from pydantic_settings import BaseSettings, SettingsConfigDict


class MaterialSettings(BaseSettings):
    """Material info settings."""

    name_min_lenght = 3
    name_max_lenght = 80
    description_min_lenght = 3
    description_max_lenght = 10000

    model_config = SettingsConfigDict(env_prefix="material_")


material_settings = MaterialSettings()
