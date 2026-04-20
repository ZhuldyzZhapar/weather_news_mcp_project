from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Intent = Literal["weather", "news", "both", "unknown"]
DayTarget = Literal["today", "tomorrow"]


@dataclass
class QueryPlan:
    intent: Intent
    city: str | None = None
    day: DayTarget = "today"
    news_topic: str | None = None
    wants_headlines: bool = False
    raw_query: str = ""


WEATHER_KEYWORDS = {
    "weather", "temperature", "forecast", "rain", "raining", "snow", "sunny",
    "cloudy", "wind", "humidity", "hot", "cold", "storm", "umbrella"
}
NEWS_KEYWORDS = {
    "news", "headline", "headlines", "latest", "article", "articles", "breaking"
}

CITIES_PATTERN = re.compile(
    r"\b(?:in|at|for)\s+([A-ZА-ЯӘІҢҒҮҰҚӨҺ][\w\-.' ]{1,40})",
    flags=re.IGNORECASE,
)
TOPIC_PATTERN = re.compile(
    r"(?:news\s+(?:about|on)|headlines\s+(?:about|on)|about)\s+([\w\-.,' ]{2,80})",
    flags=re.IGNORECASE,
)


def _contains_any(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in keywords)


def _extract_city(query: str, memory: dict) -> str | None:
    match = CITIES_PATTERN.search(query)
    if match:
        candidate = match.group(1).strip(" ?!.,")
        # avoid false positives like 'news about ai'
        if len(candidate.split()) <= 4:
            return candidate

    lowered = query.lower().strip()
    if any(p in lowered for p in ["there", "that city", "same city", "same place"]):
        return memory.get("last_city")

    return memory.get("last_city") if re.search(r"\b(tomorrow|today|there)\b", lowered) else None


def _extract_news_topic(query: str, memory: dict) -> str | None:
    match = TOPIC_PATTERN.search(query)
    if match:
        return match.group(1).strip(" ?!.,")

    lowered = query.lower().strip()
    if any(p in lowered for p in ["same topic", "that topic", "more on this"]):
        return memory.get("last_topic")

    return None


def build_query_plan(query: str, memory: dict | None = None) -> QueryPlan:
    memory = memory or {}
    lowered = query.lower()

    has_weather = _contains_any(lowered, WEATHER_KEYWORDS) or bool(re.search(r"\bwill it rain\b", lowered))
    has_news = _contains_any(lowered, NEWS_KEYWORDS)

    wants_headlines = bool(re.search(r"\b(latest headlines|latest news|top headlines|what'?s happening)\b", lowered))
    day: DayTarget = "tomorrow" if "tomorrow" in lowered else "today"

    city = _extract_city(query, memory)
    topic = _extract_news_topic(query, memory)

    # Follow-up recovery
    if not has_weather and not has_news:
        if city and re.search(r"\b(tomorrow|today|rain|forecast|temperature|weather)\b", lowered):
            has_weather = True
        elif topic or re.search(r"\b(headlines|latest|news)\b", lowered):
            has_news = True

    if has_weather and has_news:
        intent: Intent = "both"
    elif has_weather:
        intent = "weather"
    elif has_news:
        intent = "news"
    else:
        intent = "unknown"

    return QueryPlan(
        intent=intent,
        city=city,
        day=day,
        news_topic=topic,
        wants_headlines=wants_headlines,
        raw_query=query,
    )
