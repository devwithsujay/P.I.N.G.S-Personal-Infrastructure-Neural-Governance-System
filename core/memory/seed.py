import logging
from core.memory.persistent import add_knowledge

logger = logging.getLogger("pings.memory.seed")

SEED_DOCUMENTS = [
    {
        "content": "P.I.N.G.S (Personal Intelligent Neural Gateway System) is a self-hosted AI assistant platform. It uses opencode as the agent execution engine, Zen models for LLM inference, and ChromaDB for vector memory storage.",
        "category": "system",
    },
    {
        "content": "The system architecture includes a FastAPI gateway, opencode CLI integration, Zen models (free tier) for text, NVIDIA NIM for vision, ChromaDB for vector memory, and SQLite for structured data.",
        "category": "system",
    },
    {
        "content": "For homelab management, PINGS uses SSH to connect to remote servers and manage Docker containers. Commands include listing containers, starting/stopping/restarting services, and viewing logs.",
        "category": "homelab",
    },
    {
        "content": "The research agent can decompose complex topics into sub-queries, search multiple sources, synthesize findings, and render HTML reports. Modes include quick, balanced, and deep research.",
        "category": "research",
    },
    {
        "content": "PINGS supports multiple AI agents: HomeLab (infrastructure), Research (web research), CodeGen (code generation), and Report (document generation). Each agent has specialized tools and capabilities.",
        "category": "agents",
    },
    {
        "content": "The task management system supports creating tasks with priorities (low, medium, high, urgent), due dates, and status tracking (pending, in_progress, done). Scheduled tasks can run on cron expressions.",
        "category": "tasks",
    },
    {
        "content": "Security layers include danger pattern detection (blocks destructive commands), confirmation requirements for risky actions, and sandboxed file operations limited to the workspace directory.",
        "category": "security",
    },
    {
        "content": "The proactive scheduler runs periodic checks: homelab health monitoring, overdue task notifications, and scheduled task execution. Notifications can be sent via Telegram and ntfy.",
        "category": "proactive",
    },
    {
        "content": "Fastembed with all-MiniLM-L6-v2 model is used for generating embeddings. This runs ONNX inference locally without requiring PyTorch, reducing memory footprint significantly.",
        "category": "embedding",
    },
    {
        "content": "Browser tool uses SearXNG as primary search engine, with DuckDuckGo as fallback. URL fetching extracts readable text content from web pages, stripping navigation and scripts.",
        "category": "browser",
    },
    {
        "content": "The SSH tool uses paramiko for secure connections. It supports both key-based and password authentication. All SSH commands are executed with timeout protection.",
        "category": "ssh",
    },
    {
        "content": "File operations are sandboxed to /app/workspace. Path validation prevents directory traversal attacks. Files larger than 1MB are blocked for reading. All operations are async.",
        "category": "files",
    },
]


async def seed_chroma_on_startup() -> int:
    try:
        from core.memory.chroma import chroma_memory
        existing = await chroma_memory.count()
        if existing and existing > 0:
            logger.info(f"ChromaDB already has {existing} entries, skipping seed")
            return 0
    except Exception:
        logger.debug("Could not check ChromaDB count, proceeding with seed")

    count = 0
    for doc in SEED_DOCUMENTS:
        try:
            await add_knowledge(
                content=doc["content"],
                category=doc["category"],
                metadata={"source": "seed", "type": "system_knowledge"},
            )
            count += 1
        except Exception as e:
            logger.warning(f"Failed to seed document ({doc['category']}): {e}")
    logger.info(f"Seeded {count}/{len(SEED_DOCUMENTS)} knowledge documents")
    return count
