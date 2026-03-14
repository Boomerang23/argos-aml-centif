from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder values that must not be used in production for JWT_SECRET / ONBOARDING_LINK_SECRET
_UNSAFE_SECRET_VALUES = frozenset({
    "change-me",
    "change-me-too",
    "change-this-in-prod",
    "change-me-in-production",
    "change-me-too-in-production",
})


def _validate_production_secrets(s: "Settings") -> None:
    """In production, refuse to start if secrets are missing or still placeholders."""
    env = (s.ENVIRONMENT or "").strip().lower()
    if env not in ("production", "prod"):
        return
    errors: list[str] = []
    for name, value in (
        ("JWT_SECRET", s.JWT_SECRET),
        ("ONBOARDING_LINK_SECRET", s.ONBOARDING_LINK_SECRET),
    ):
        v = (value or "").strip()
        if not v:
            errors.append(f"{name} is required in production and must not be empty.")
        elif v.lower() in _UNSAFE_SECRET_VALUES:
            errors.append(
                f"{name} must not use a placeholder value in production "
                f"(current value looks like a default). Set a strong secret in your environment."
            )
    if errors:
        msg = "Production secrets validation failed: " + " ".join(errors)
        raise SystemExit(msg)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # When set to production/prod, JWT_SECRET and ONBOARDING_LINK_SECRET are validated at startup
    ENVIRONMENT: str = "development"

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

    # Onboarding links (token signing + public URL for generated links)
    ONBOARDING_LINK_SECRET: str = "change-me-too"
    ONBOARDING_LINK_TTL_HOURS: int = 72
    ONBOARDING_BASE_URL: str = "http://127.0.0.1:8000"
    ONBOARDING_UPLOAD_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB max per file

    # CORS (comma-separated list of allowed origins; default = local dev)
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Redis (optional). When set, login rate limiting uses Redis for multi-worker/replica support.
    REDIS_URL: str | None = None

    # Login rate limit: attempts per IP per window (used by Redis and in-memory backends)
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60


settings = Settings()
_validate_production_secrets(settings)