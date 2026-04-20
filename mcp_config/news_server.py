from __future__ import annotations

import logging
import os
import re
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
import html

import httpx
from mcp.server.fastmcp import FastMCP


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("news-server")

# Optional provider with token
THENEWS_BASE = "https://api.thenewsapi.com/v1/news/top"
THENEWS_TOKEN = os.getenv("THE_NEWS_API_TOKEN")

# No-key RSS feeds
GOOGLE_NEWS_TOP = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
GOOGLE_NEWS_SEARCH = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


async def _get_text(url: str, params: dict[str, Any] | None = None) -> str:
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.text


async def _get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    # убрать HTML-теги
    value = re.sub(r"<[^>]+>", " ", value)

    # декодировать HTML entities
    value = html.unescape(value)

    # убрать лишние пробелы
    value = re.sub(r"\s+", " ", value).strip()

    return value


def _parse_google_news_rss(xml_text: str, limit: int) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")

    articles: list[dict[str, str]] = []
    for item in items[:limit]:
        title = _clean_text(item.findtext("title")) or "Untitled"
        link = _clean_text(item.findtext("link"))
        description = _clean_text(item.findtext("description")) or "No summary available."
        pub_date = _clean_text(item.findtext("pubDate"))
        source_elem = item.find("source")
        source = _clean_text(source_elem.text if source_elem is not None else "Google News")

        articles.append(
            {
                "title": title,
                "summary": f"Published: {pub_date}" if pub_date else "Latest headline",
                "url": link,
                "source": source or "Google News",
            }
        )
    return articles


async def _top_headlines_from_google(limit: int) -> dict[str, Any]:
    xml_text = await _get_text(GOOGLE_NEWS_TOP)
    articles = _parse_google_news_rss(xml_text, limit)
    return {"ok": True, "provider": "Google News RSS", "articles": articles}


async def _search_news_from_google(topic: str, limit: int) -> dict[str, Any]:
    query = quote_plus(topic)
    url = GOOGLE_NEWS_SEARCH.format(query=query)
    xml_text = await _get_text(url)
    articles = _parse_google_news_rss(xml_text, limit)
    return {"ok": True, "provider": "Google News RSS", "articles": articles}


def _normalize_thenews_articles(items: list[dict[str, Any]], limit: int) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for article in items[:limit]:
        normalized.append(
            {
                "title": article.get("title", "Untitled"),
                "summary": article.get("description") or article.get("snippet") or "No summary available.",
                "url": article.get("url", ""),
                "source": article.get("source", "TheNews API"),
            }
        )
    return normalized


async def _search_news_from_thenews(topic: str, limit: int) -> dict[str, Any]:
    payload = await _get_json(
        THENEWS_BASE,
        {
            "api_token": THENEWS_TOKEN,
            "search": topic,
            "language": "en",
            "limit": limit,
        },
    )
    return {
        "ok": True,
        "provider": "TheNews API",
        "articles": _normalize_thenews_articles(payload.get("data", []), limit),
    }


@mcp.tool()
async def get_top_headlines(limit: int = 5) -> dict[str, Any]:
    """Get latest headlines without requiring API keys by default."""
    try:
        return await _top_headlines_from_google(limit)
    except Exception as exc:
        logger.exception("get_top_headlines failed")
        return {"ok": False, "error": str(exc), "articles": []}


@mcp.tool()
async def search_news(topic: str, limit: int = 5) -> dict[str, Any]:
    """Search news by topic. Uses TheNews API if token exists, otherwise Google News RSS."""
    try:
        if THENEWS_TOKEN:
            return await _search_news_from_thenews(topic, limit)

        result = await _search_news_from_google(topic, limit)

        # fallback: if no results for exact topic, try adding "news"
        if not result.get("articles"):
            result = await _search_news_from_google(f"{topic} news", limit)

        return result
    except Exception as exc:
        logger.exception("search_news failed")
        return {"ok": False, "error": str(exc), "articles": []}


if __name__ == "__main__":
    mcp.run()
