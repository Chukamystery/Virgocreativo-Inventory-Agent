from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Inventory Agent API"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/inventory_agent.db"
    
    openai_vector_store_id: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    allow_agent_writes: bool = False

    supabase_url: str = ""
    supabase_publishable_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()

