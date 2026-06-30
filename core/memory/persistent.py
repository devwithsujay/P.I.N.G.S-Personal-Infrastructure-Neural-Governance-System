import logging
import uuid
from typing import Any, Dict, List, Optional

from core.memory.chroma import chroma_memory
from core.memory.embedder import encode
from core.memory.db import save_memory_entry, get_memory_entries

logger = logging.getLogger("pings.memory.persistent")


async def add_knowledge(content: str, category: str = "general", session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    entry_id = str(uuid.uuid4())

    await save_memory_entry(content=content, session_id=session_id, category=category, embedding_id=entry_id)

    try:
        embeddings = await encode([content])
        meta = metadata or {}
        meta["category"] = category
        if session_id:
            meta["session_id"] = session_id
        await chroma_memory.add(
            ids=[entry_id],
            documents=[content],
            embeddings=embeddings,
            metadatas=[meta],
        )
        logger.info(f"Added knowledge: {entry_id} ({category})")
    except Exception as e:
        logger.warning(f"Chroma write failed for {entry_id}: {e}")

    return entry_id


async def search_knowledge(query: str, n_results: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        embeddings = await encode([query])
        where = {"category": category} if category else None
        results = await chroma_memory.query(
            query_embeddings=embeddings,
            n_results=n_results,
            where=where,
        )
        return results
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        entries = await get_memory_entries(category=category, limit=n_results)
        return [{"id": str(e.get("id", "")), "document": e.get("content", ""), "distance": 0} for e in entries]


async def get_knowledge_by_category(category: str, limit: int = 20) -> List[Dict[str, Any]]:
    return await get_memory_entries(category=category, limit=limit)


async def delete_knowledge(entry_id: str) -> bool:
    try:
        await chroma_memory.delete(ids=[entry_id])
        return True
    except Exception as e:
        logger.error(f"Knowledge delete failed: {e}")
        return False


async def get_memory_stats() -> Dict[str, Any]:
    from core.memory.db import get_db
    chroma_health = await chroma_memory.health_check()
    total = 0
    categories: Dict[str, int] = {}
    try:
        db = await get_db()
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM memory_entries")
        row = await cursor.fetchone()
        total = row["cnt"] if row else 0
        cursor2 = await db.execute("SELECT category, COUNT(*) as cnt FROM memory_entries GROUP BY category")
        rows = await cursor2.fetchall()
        for r in rows:
            categories[r["category"]] = r["cnt"]
        await db.close()
    except Exception:
        pass
    return {
        "total_entries": total,
        "categories": categories,
        "chroma_status": chroma_health.get("status", "unknown"),
        "sqlite_status": "healthy",
    }
