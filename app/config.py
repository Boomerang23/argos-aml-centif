from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://argos:argos@localhost:5432/argos_centif"
    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60 * 12

    # OpenSanctions (optionnel au début si tu veux mocker)
    OPENSANCTIONS_API_KEY: str | None = None
    OPENSANCTIONS_BASE_URL: str = "https://api.opensanctions.org"

    # Storage S3-compatible
    S3_ENDPOINT_URL: str | None = None   # ex: http://localhost:9000
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = "argos-centif"
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None

    # Onboarding links
    ONBOARDING_LINK_SECRET: str = "change-me-too"
    ONBOARDING_LINK_TTL_HOURS: int = 72

settings = Settings()