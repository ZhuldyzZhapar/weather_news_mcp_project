from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .mcp_client import MCPToolClient, MCPToolError
from .parser import QueryPlan, build_query_plan


@dataclass
class AgentResponse:
    text: str
    plan: QueryPlan
    weather_data: dict[str, Any] | None = None
    news_data: dict[str, Any] | None = None


class WeatherNewsOrchestrator:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.client = MCPToolClient(self.project_root)
        self.memory: dict[str, Any] = {}

    def answer(self, user_query: str) -> AgentResponse:
        plan = build_query_plan(user_query, self.memory)

        if plan.intent == "unknown":
            return AgentResponse(
                text=(
                    "I can help with weather, news, or both. "
                    "Try something like 'What's the weather in Almaty?' or 'Latest news about AI'."
                ),
                plan=plan,
            )

        weather_data = None
        news_data = None
        blocks: list[str] = []

        if plan.intent in {"weather", "both"}:
            if not plan.city:
                return AgentResponse(
                    text="Please mention a city or location for the weather request.",
                    plan=plan,
                )

            try:
                weather_tool = "get_weather_forecast" if plan.day == "tomorrow" else "get_current_weather"
                weather_data = self.client.call_tool_sync(
                    "mcp_config/weather_server.py",
                    weather_tool,
                    {"city": plan.city},
                )
                blocks.append(self._format_weather(weather_data, plan))
                self.memory["last_city"] = weather_data.get("resolved_name", plan.city)
            except MCPToolError as exc:
                blocks.append(f"Weather service error: {exc}")

        if plan.intent in {"news", "both"}:
            try:
                if plan.news_topic:
                    news_data = self.client.call_tool_sync(
                        "mcp_config/news_server.py",
                        "search_news",
                        {"topic": plan.news_topic, "limit": 5},
                    )
                    self.memory["last_topic"] = plan.news_topic
                else:
                    news_data = self.client.call_tool_sync(
                        "mcp_config/news_server.py",
                        "get_top_headlines",
                        {"limit": 5},
                    )
                blocks.append(self._format_news(news_data, plan))
            except MCPToolError as exc:
                blocks.append(f"News service error: {exc}")

        if not blocks:
            blocks.append("I couldn't get a response from the external services right now.")

        self.memory["last_intent"] = plan.intent
        return AgentResponse(
            text="\n\n".join(blocks),
            plan=plan,
            weather_data=weather_data,
            news_data=news_data,
        )

    @staticmethod
    def _format_weather(data: dict[str, Any], plan: QueryPlan) -> str:
        if not data.get("ok", True):
            return f"Weather: {data.get('error', 'Unknown error')}"

        if plan.day == "today":
            return (
                f"### Weather in {data['resolved_name']}\n"
                f"- Temperature: {data['temperature_c']}°C\n"
                f"- Condition: {data['condition']}\n"
                f"- Wind: {data['wind_speed_kmh']} km/h\n"
                f"- Time: {data['observed_at']}"
            )

        return (
            f"### Forecast for {data['resolved_name']} (tomorrow)\n"
            f"- Min / Max: {data['min_temp_c']}°C / {data['max_temp_c']}°C\n"
            f"- Rain probability: {data['rain_probability_percent']}%\n"
            f"- Expected condition: {data['condition']}\n"
            f"- Advice: {'Take an umbrella.' if data['rain_probability_percent'] >= 40 else 'Rain is not likely.'}"
        )

    @staticmethod
    def _format_news(data: dict[str, Any], plan: QueryPlan) -> str:
        if not data.get("ok", True):
            return f"News: {data.get('error', 'Unknown error')}"

        title = f"### News about {plan.news_topic}" if plan.news_topic else "### Latest headlines"
        lines = [title]
        articles = data.get("articles", [])
        if not articles:
            return title + "\n- No matching articles found."

        for idx, article in enumerate(articles, start=1):
            source = article.get("source") or "Unknown source"
            summary = article.get("summary") or "No summary available."
            lines.append(
                f"{idx}. **{article.get('title', 'Untitled')}**\n"
                f"   - Source: {source}\n"
                f"   - Summary: {summary}\n"
                f"   - URL: {article.get('url', '')}"
            )
        return "\n".join(lines)
