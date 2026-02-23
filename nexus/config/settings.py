from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Caminhos
    nexus_db_path: str = "./nexus.db"
    nexus_notes_dir: str = "./notes"

    # Portas das APIs
    data_api_port: int = 3333
    cortex_api_port: int = 4444

    # Chaves de Terceiros (Opcionais)
    google_api_key: str | None = None

    # Configuração do Pydantic para ler o .env ignorando variáveis extras
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Instância singleton para ser importada por toda a aplicação
settings = Settings()
