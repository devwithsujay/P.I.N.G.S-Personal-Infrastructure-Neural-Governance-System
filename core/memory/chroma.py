import logging
import asyncio
from typing import Any, Dict, List, Optional

import httpx

from core.config import settings

logger = logging.getLogger("pings.memory.chroma")


class ChromaMemory:
    def __init__(self) -> None:
        self.url = settings.CHROMA_URL
        self.collection = "pings_knowledge"
        self._collection_id: Optional[str] = None

    async def _ensure_collection(self) -> str:
        if self._collection_id:
            return self._collection_id
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(f"{self.url}/api/v1/collections/{self.collection}")
                if resp.status_code == 200:
                    data = resp.json()
                    self._collection_id = data.get("id", self.collection)
                    return self._collection_id

                resp = await client.post(
                    f"{self.url}/api/v1/collections",
                    json={"name": self.collection, "metadata": {"hnsw:space": "cosine"}},
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    self._collection_id = data.get("id", self.collection)
                    return self._collection_id

                list_resp = await client.get(f"{self.url}/api/v1/collections")
                if list_resp.status_code == 200:
                    for col in list_resp.json():
                        if col.get("name") == self.collection:
                            self._collection_id = col.get("id", self.collection)
                            return self._collection_id

            except Exception as e:
                logger.error(f"Failed to ensure Chroma collection: {e}")
                raise
        return self.collection

    async def add(self, ids: List[str], documents: List[str], embeddings: Optional[List[List[float]]] = None, metadatas: Optional[List[Dict[str, Any]]] = None) -> bool:
        try:
            collection_id = await self._ensure_collection()
            payload: Dict[str, Any] = {
                "ids": ids,
                "documents": documents,
            }
            if embeddings:
                payload["embeddings"] = embeddings
            if metadatas:
                payload["metadatas"] = metadatas

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.url}/api/v1/collections/{collection_id}/add",
                    json=payload,
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Chroma add failed: {e}")
            return False

    async def query(self, query_embeddings: List[List[float]], n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            collection_id = await self._ensure_collection()
            payload: Dict[str, Any] = {
                "query_embeddings": query_embeddings,
                "n_results": n_results,
            }
            if where:
                payload["where"] = where

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.url}/api/v1/collections/{collection_id}/query",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            results: List[Dict[str, Any]] = []
            ids = data.get("ids", [[]])[0] if data.get("ids") else []
            docs = data.get("documents", [[]])[0] if data.get("documents") else []
            distances = data.get("distances", [[]])[0] if data.get("distances") else []
            metadatas_list = data.get("metadatas", [[]])[0] if data.get("metadatas") else []

            for i in range(len(ids)):
                entry: Dict[str, Any] = {
                    "id": ids[i] if i < len(ids) else "",
                    "document": docs[i] if i < len(docs) else "",
                    "distance": distances[i] if i < len(distances) else 0,
                }
                if i < len(metadatas_list) and metadatas_list[i]:
                    entry["metadata"] = metadatas_list[i]
                results.append(entry)
            return results
        except Exception as e:
            logger.error(f"Chroma query failed: {e}")
            return []

    def _query_sync(self, query_embeddings: List[List[float]], n_results: int = 5) -> List[Dict[str, Any]]:
        try:
            import chromadb
            client = chromadb.HttpClient(host=self.url.replace("http://", "").replace("https://", "").split(":")[0], port=int(self.url.split(":")[-1]))
            collection = client.get_or_create_collection(self.collection)
            results = collection.query(query_embeddings=query_embeddings, n_results=n_results)
            output: List[Dict[str, Any]] = []
            ids = results.get("ids", [[]])[0] if results.get("ids") else []
            docs = results.get("documents", [[]])[0] if results.get("documents") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []
            for i in range(len(ids)):
                output.append({
                    "id": ids[i] if i < len(ids) else "",
                    "document": docs[i] if i < len(docs) else "",
                    "distance": distances[i] if i < len(distances) else 0,
                })
            return output
        except Exception as e:
            logger.error(f"Chroma sync query failed: {e}")
            return []

    async def delete(self, ids: List[str]) -> bool:
        try:
            collection_id = await self._ensure_collection()
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.url}/api/v1/collections/{collection_id}/delete",
                    json={"ids": ids},
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Chroma delete failed: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/api/v1/heartbeat")
                resp.raise_for_status()
                return {"status": "healthy", "url": self.url}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "url": self.url}


chroma_memory = ChromaMemory()
