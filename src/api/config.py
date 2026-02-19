import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Consolidated application configuration."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime
    env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"
    use_in_memory_adapters: bool = False

    # GCP Credentials
    google_application_credentials: str | None = None

    # Firestore
    firestore_project_id: str = ""
    firestore_database_id: str = "(default)"
    firestore_collection: str = "generators"

    # Google Cloud Storage
    gcs_project_id: str = ""
    gcs_bucket: str = ""
    gcs_upload_url_expiry_seconds: int = 600

    def validate_gcp_settings(self) -> None:
        """Ensure required GCP settings are configured."""
        if self.use_in_memory_adapters:
            return

        # Explicitly export credentials to environment if provided in .env
        if self.google_application_credentials:
            # If the path is relative, make it absolute relative to the .env file / app root
            path = Path(self.google_application_credentials)
            if not path.is_absolute():
                path = (Path(__file__).parent / path).resolve()

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)

        missing: list[str] = []
        if not self.firestore_project_id:
            missing.append("FIRESTORE_PROJECT_ID")
        if not self.firestore_collection:
            missing.append("FIRESTORE_COLLECTION")
        if not self.gcs_project_id:
            missing.append("GCS_PROJECT_ID")
        if not self.gcs_bucket:
            missing.append("GCS_BUCKET")

        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"Missing required GCP settings: {missing_text}")


# Singleton instance
settings = AppConfig()
