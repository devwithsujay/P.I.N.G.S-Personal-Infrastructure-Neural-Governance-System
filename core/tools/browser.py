import logging
import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx

from core.config import settings
from core.tools.base import BaseTool

logger = logging.getLogger("pings.tools.browser")


async def web_search(query: str, engine: str = "auto") -> str:
    if engine == "searxng" or engine == "auto":
        try:
            results = await _search_searxng(query)
            if results:
                return results
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")
            if engine == "searxng":
                return f"SearXNG search failed: {e}"

    if engine == "serpapi" or engine == "auto":
        try:
            results = await _search_serpapi(query)
            if results:
                return results
        except Exception as e:
            logger.warning(f"SerpAPI search failed: {e}")

    if engine == "ddg" or engine == "auto":
        try:
            results = await _search_ddg(query)
            if results:
                return results
        except Exception as e:
            logger.warning(f"DDG search failed: {e}")

    return f"No search results found for: {query}"


async def _search_searxng(query: str) -> str:
    url = f"{settings.SEARXNG_URL}/search"
    params = {"q": query, "format": "json", "categories": "general"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return ""

    lines = [f"SearXNG results for: {query}\n"]
    for i, r in enumerate(results[:8], 1):
        title = r.get("title", "No title")
        snippet = r.get("content", "")
        link = r.get("url", "")
        lines.append(f"{i}. **{title}**\n   {link}\n   {snippet[:200]}\n")
    return "\n".join(lines)


async def _search_serpapi(query: str) -> str:
    api_key = settings.SERPAPI_KEY
    if not api_key:
        return ""
    url = "https://serpapi.com/search"
    params = {"q": query, "api_key": api_key, "engine": "google", "num": 8}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("organic_results", [])
    if not results:
        return ""

    lines = [f"SerpAPI results for: {query}\n"]
    for i, r in enumerate(results[:8], 1):
        title = r.get("title", "No title")
        snippet = r.get("snippet", "")
        link = r.get("link", "")
        lines.append(f"{i}. **{title}**\n   {link}\n   {snippet[:200]}\n")
    return "\n".join(lines)


async def _search_ddg(query: str) -> str:
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (PINGS Bot)"}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        text = resp.text

    import re
    results: List[Dict[str, str]] = []
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL)
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', text, re.DOTALL)
    urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', text, re.DOTALL)

    if not titles:
        return ""

    lines = [f"DuckDuckGo results for: {query}\n"]
    for i in range(min(8, len(titles))):
        title = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else ""
        snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        link = urls[i].strip() if i < len(urls) else ""
        lines.append(f"{i+1}. **{title}**\n   {link}\n   {snippet[:200]}\n")
    return "\n".join(lines)


async def fetch_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (PINGS Bot)"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "text/html" in content_type:
                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self) -> None:
                        super().__init__()
                        self.result: List[str] = []
                        self.skip = False

                    def handle_starttag(self, tag: str, attrs: Any) -> None:
                        if tag in ("script", "style", "nav", "footer", "header"):
                            self.skip = True

                    def handle_endtag(self, tag: str) -> None:
                        if tag in ("script", "style", "nav", "footer", "header"):
                            self.skip = False

                    def handle_data(self, data: str) -> None:
                        if not self.skip:
                            text = data.strip()
                            if text:
                                self.result.append(text)

                extractor = TextExtractor()
                extractor.feed(resp.text)
                full_text = " ".join(extractor.result)
                if len(full_text) > 8000:
                    full_text = full_text[:8000] + "\n...[truncated]"
                return full_text
            else:
                return resp.text[:8000]
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return f"Failed to fetch URL: {e}"


class BrowserTool(BaseTool):
    name = "browser"
    description = "Search the web and fetch page content"
    trigger_patterns = ["search", "look up", "find online", "google", "browse", "what is", "who is"]
    priority = 30

    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        query = message
        for prefix in ["search for ", "search ", "look up ", "google ", "find online "]:
            if message.lower().startswith(prefix):
                query = message[len(prefix):]
                break

        if query.startswith("http://") or query.startswith("https://"):
            return await fetch_url(query)

        logger.info(f"Browser search: {query}")
        return await web_search(query)
