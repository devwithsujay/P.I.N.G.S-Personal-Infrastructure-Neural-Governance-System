import logging
import os
from typing import Any, Dict, Optional

from core.agents.opencode_engine import run_opencode_task
from core.tools.file_tool import write_file

logger = logging.getLogger("pings.agents.codegen")

CODEGEN_SYSTEM_PROMPT = """You are a code generation assistant. When generating code:
1. Write complete, production-ready code
2. Include proper error handling
3. Follow best practices for the language
4. Add type hints where applicable
5. Explain what the code does briefly
"""


async def handle_codegen(message: str, system_prompt: str = "", model: Optional[str] = None) -> str:
    logger.info(f"CodeGen processing: {message[:100]}")

    full_prompt = CODEGEN_SYSTEM_PROMPT
    if system_prompt:
        full_prompt = system_prompt + "\n\n" + CODEGEN_SYSTEM_PROMPT

    response = await run_opencode_task(
        task=f"Generate code for: {message}. Return the complete code with filenames in format: FILENAME:\\n```language\\ncode\\n```",
        system_context=full_prompt,
        model=model,
    )

    if response and not response.startswith("Agent error"):
        import re
        file_blocks = re.findall(r'(\S+\.(?:py|js|ts|jsx|tsx|html|css|json|yaml|yml|sh|md|txt|sql|go|rs|java|c|cpp|h))\s*[:\n]\s*```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        saved_files = []
        for filename, code in file_blocks:
            filename = filename.strip().strip("`")
            code = code.strip()
            if filename and code:
                result = await write_file(filename, code)
                if not result.startswith("Error"):
                    saved_files.append(filename)

        if saved_files:
            response += f"\n\nSaved {len(saved_files)} file(s): {', '.join(saved_files)}"

        from core.memory.persistent import add_knowledge
        await add_knowledge(
            content=f"Generated code for: {message[:200]}",
            category="codegen",
            metadata={"topic": message[:100]},
        )

    return response
