from __future__ import annotations

import asyncio
from typing import Any, Generic, TypeVar, Type

from google.cloud import firestore
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FirestoreRepository(Generic[T]):
    """Generic repository for Firestore with async/sync detection."""

    def __init__(
        self,
        project_id: str,
        database_id: str,
        collection_name: str,
        model_type: Type[T]
    ):
        self.project_id = project_id
        self.database_id = database_id
        self.collection_name = collection_name
        self.model_type = model_type
        
        if hasattr(firestore, "AsyncClient"):
            self._client = firestore.AsyncClient(project=project_id, database=database_id)
        else:
            self._client = firestore.Client(project=project_id, database=database_id)
            
        self._collection = self._client.collection(collection_name)

    async def _run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Helper to run a method asynchronously or in an executor if sync."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def get(self, document_id: str) -> T | None:
        doc_ref = self._collection.document(document_id)
        snapshot = await self._run(doc_ref.get)
        if not snapshot.exists:
            return None
        return self.model_type.model_validate({"id": snapshot.id, **(snapshot.to_dict() or {})})

    async def delete(self, document_id: str) -> bool:
        doc_ref = self._collection.document(document_id)
        snapshot = await self._run(doc_ref.get)
        if not snapshot.exists:
            return False
        await self._run(doc_ref.delete)
        return True

    async def list_all(self, filters: list[tuple[str, str, Any]] | None = None) -> list[T]:
        query = self._collection
        if filters:
            for field_path, op, value in filters:
                query = query.where(field_path=field_path, op_string=op, value=value)
        
        items = []
        try:
            # Try async iteration first
            async for doc in query.stream():
                items.append(self.model_type.model_validate({"id": doc.id, **(doc.to_dict() or {})}))
        except (TypeError, AttributeError):
            # Fallback to sync iteration if client is sync
            docs = await self._run(lambda: list(query.stream()))
            for doc in docs:
                items.append(self.model_type.model_validate({"id": doc.id, **(doc.to_dict() or {})}))
        
        return items

    async def save(self, document_id: str, data: T) -> T:
        doc_ref = self._collection.document(document_id)
        payload = data.model_dump(mode="json", exclude_none=True)
        # Ensure ID is not in the body if it's the document name, but we usually keep it for portability
        await self._run(doc_ref.set, payload)
        return data
