from __future__ import annotations

from config import settings
from repositories.firestore import FirestoreMetadataAdapter
from repositories.memory import InMemoryMetadataAdapter
from repositories.storage import FakeSignedUploadAdapter, GCSSignedUploadAdapter
from services.generator_service import GeneratorService


def build_generator_service() -> GeneratorService:
    if settings.use_in_memory_adapters:
        return GeneratorService(
            metadata=InMemoryMetadataAdapter(),
            storage=FakeSignedUploadAdapter(),
        )

    settings.validate_gcp_settings()
    return GeneratorService(
        metadata=FirestoreMetadataAdapter(
            project_id=settings.firestore_project_id or "",
            database_id=settings.firestore_database_id,
            collection_name=settings.firestore_collection,
        ),
        storage=GCSSignedUploadAdapter(
            project_id=settings.gcs_project_id or "",
            bucket_name=settings.gcs_bucket or "",
            expiry_seconds=settings.gcs_upload_url_expiry_seconds,
        ),
    )
