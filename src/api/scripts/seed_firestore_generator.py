from __future__ import annotations

import argparse
import json
from pathlib import Path

from google.cloud import firestore

try:
    from ..config import FirestoreSettings
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from config import FirestoreSettings


def _load_payload(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Mock metadata payload must be a JSON object")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed one mock generator document in Firestore.")
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().parents[1] / "mock_data" / "generator_metadata.json"),
        help="Path to generator metadata JSON file.",
    )
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Optional Firestore document id override. Defaults to payload['id'].",
    )
    args = parser.parse_args()

    payload = _load_payload(Path(args.input))
    settings = FirestoreSettings.from_env()
    if not settings.project_id:
        raise RuntimeError("Missing project id. Set GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT.")

    doc_id = args.doc_id or payload.get("id")
    if not doc_id:
        raise RuntimeError("Document id is required. Provide --doc-id or include 'id' in payload.")

    db = firestore.Client(project=settings.project_id, database=settings.database_id)
    db.collection(settings.collection).document(str(doc_id)).set(payload)

    print(
        f"Seeded document '{doc_id}' into "
        f"projects/{settings.project_id}/databases/{settings.database_id}/documents/{settings.collection}"
    )


if __name__ == "__main__":
    main()
