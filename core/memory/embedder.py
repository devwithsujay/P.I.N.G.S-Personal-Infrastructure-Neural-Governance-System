import logging
import asyncio
from typing import List

from core.config import settings

logger = logging.getLogger("pings.memory.embedder")

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
            _model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


async def encode(texts: List[str]) -> List[List[float]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _encode_sync, texts)


def _encode_sync(texts: List[str]) -> List[List[float]]:
    model = _get_model()
    embeddings = list(model.embed(texts))
    return [emb.tolist() for emb in embeddings]


async def encode_single(text: str) -> List[float]:
    results = await encode([text])
    return results[0]
