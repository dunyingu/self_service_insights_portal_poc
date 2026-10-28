from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # LLM
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    azure_openai_api_key: str | None = Field(default=None, alias='AZURE_OPENAI_API_KEY')
    azure_openai_api_version: str | None = Field(default=None, alias='AZURE_OPENAI_API_VERSION')
    azure_openai_endpoint: str | None = Field(default=None, alias='AZURE_OPENAI_ENDPOINT')

    # Embeddings
    embedding_model: str | None = Field(default="text-embedding-3-large", alias='EMBEDDING_MODEL')

    # Snowflake
    snowflake_account: str | None = Field(default=None, alias='SNOWFLAKE_ACCOUNT')
    snowflake_user: str | None = Field(default=None, alias='SNOWFLAKE_USER')
    snowflake_password: str | None = Field(default=None, alias='SNOWFLAKE_PASSWORD')
    snowflake_role: str | None = Field(default=None, alias='SNOWFLAKE_ROLE')
    snowflake_warehouse: str | None = Field(default=None, alias='SNOWFLAKE_WAREHOUSE')
    snowflake_database: str | None = Field(default=None, alias='SNOWFLAKE_DATABASE')
    snowflake_schema: str | None = Field(default=None, alias='SNOWFLAKE_SCHEMA')

    # Vector tables
    semantic_model_table: str | None = Field(default=None, alias='SEMANTIC_MODEL_TABLE')  # e.g. ANALYTICS.SEMANTIC_EMB
    business_docs_table: str | None = Field(default=None, alias='BUSINESS_DOCS_TABLE')    # e.g. ANALYTICS.DOCS_EMB

    # Misc
    use_fake_db: bool = Field(default=False, alias='USE_FAKE_DB')
    checkpoint_db: str | None = Field(default=None, alias='CHECKPOINT_DB')

    # Email
    email_user: str | None = Field(default=None, alias='EMAIL_USER')
    email_app_password: str | None = Field(default=None, alias='EMAIL_APP_PASSWORD')

    model_config = dict(env_file='.env', extra='ignore')

settings = Settings()
