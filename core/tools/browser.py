import logging
import asyncio
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx

from core.config import settings

logger = logging.getLogger("pings.tools.browser")

_search_sem = asyncio.Semaphore(2)


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str


def is_usable(source: "Source") -> bool:
    if not source.full_text:
        return False
    words = source.full_text.split()
    if len(words) < 300:
        return False
    paywall_markers = [
        "subscribe to continue", "payment required", "access denied",
        "please log in", "sign in to read", "membership required",
        "this content is reserved for", "upgrade to premium",
    ]
    lower_text = source.full_text.lower()
    if any(marker in lower_text for marker in paywall_markers):
        return False
    return True


def _content_hash(text: str) -> str:
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()


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
    async with _search_sem:
        url = f"{settings.SEARXNG_URL}/search"
        params = {"q": query, "format": "json", "categories": "general"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        await asyncio.sleep(0.5)

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


async def fetch_url(url: str, timeout: int = 20) -> str:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
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


async def search_structured(query: str) -> List[SearchResult]:
    results: List[SearchResult] = []

    async with _search_sem:
        for attempt in range(2):
            try:
                url = f"{settings.SEARXNG_URL}/search"
                params = {"q": query, "format": "json", "categories": "general"}
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                await asyncio.sleep(0.5)

                for r in data.get("results", [])[:10]:
                    results.append(SearchResult(
                        url=r.get("url", ""),
                        title=r.get("title", ""),
                        snippet=r.get("content", ""),
                    ))
                if results:
                    return results
                logger.warning(f"SearXNG empty results for query (attempt {attempt+1}): {query[:80]}")
            except Exception as e:
                logger.warning(f"SearXNG search failed (attempt {attempt+1}): {e}")

            if attempt == 0:
                await asyncio.sleep(2)

    logger.error(f"SearXNG no results after retries for: {query[:80]}")
    try:
        from core.tools.ntfy import send_ntfy
        await send_ntfy(
            title="SearXNG Search Failed",
            message=f"No results after retries for: {query[:100]}",
            priority="high",
            tags="warning",
        )
    except Exception:
        pass
    return results

    try:
        api_key = settings.SERPAPI_KEY
        if api_key:
            url = "https://serpapi.com/search"
            params = {"q": query, "api_key": api_key, "engine": "google", "num": 10}
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            for r in data.get("organic_results", [])[:10]:
                results.append(SearchResult(
                    url=r.get("link", ""),
                    title=r.get("title", ""),
                    snippet=r.get("snippet", ""),
                ))
            if results:
                return results
    except Exception as e:
        logger.warning(f"SerpAPI search failed: {e}")

    try:
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0 (PINGS Bot)"}
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', text, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', text, re.DOTALL)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', text, re.DOTALL)
        for i in range(min(10, len(titles))):
            results.append(SearchResult(
                url=urls[i].strip() if i < len(urls) else "",
                title=re.sub(r"<[^>]+>", "", titles[i]).strip(),
                snippet=re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else "",
            ))
    except Exception as e:
        logger.warning(f"DDG search failed: {e}")

    return results


async def fetch_all(candidates: List[SearchResult]) -> List["Source"]:
    from core.schemas import Source
    sem = asyncio.Semaphore(settings.FETCH_CONCURRENCY)

    async def fetch_one(c: SearchResult):
        async with sem:
            try:
                text = await fetch_url(c.url, timeout=settings.FETCH_TIMEOUT_SECONDS)
                word_count = len(text.split()) if text else 0
                return Source(url=c.url, title=c.title, full_text=text, fetched=True, word_count=word_count)
            except (TimeoutError, httpx.HTTPError):
                return Source(url=c.url, title=c.title, full_text=None, fetched=False)

    results = await asyncio.gather(*[fetch_one(c) for c in candidates])
    return [r for r in results if r.fetched]


async def search_searxng_and_ddg(query: str) -> List[SearchResult]:
    return await search_structured(query)


