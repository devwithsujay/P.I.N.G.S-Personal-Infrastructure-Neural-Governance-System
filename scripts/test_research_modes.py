import asyncio
import json
import aiohttp

async def test_research(mode, topic, filename):
    async with aiohttp.ClientSession() as session:
        payload = {"topic": topic, "mode": mode, "max_sources": 5}
        async with session.post(
            "http://localhost:8000/research/start",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=240),
        ) as resp:
            data = await resp.json()
            report = data.get("report", "")
            status = data.get("status", "unknown")
            with open(f"/app/workspace/research/{filename}", "w") as f:
                f.write(report)
            print(f"DONE: {filename} ({len(report)} chars, status={status})")
            return report

async def main():
    tests = [
        ("product", "Notion", "test_product.md"),
        ("compare", "Notion vs Obsidian", "test_compare.md"),
        ("how-to", "setting up a Tailscale exit node", "test_howto.md"),
        ("fact-check", "does drinking cold water slow digestion", "test_factcheck.md"),
        ("auto", "what is retrieval-augmented generation", "test_auto.md"),
    ]
    for mode, topic, filename in tests:
        try:
            await test_research(mode, topic, filename)
        except Exception as e:
            print(f"FAIL: {filename}: {e}")

asyncio.run(main())
