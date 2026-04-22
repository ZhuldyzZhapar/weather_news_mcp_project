from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from .mcp_client import MCPToolClient, MCPToolError


SYSTEM_PROMPT = """
You are a Weather and News assistant.

Your job:
- Answer weather questions using the weather tools.
- Answer news questions using the news tools.
- If the user asks for both, use both relevant tools.
- Use tools instead of guessing.
- For current weather, use get_current_weather.
- For tomorrow's weather or rain tomorrow, use get_tomorrow_weather.
- For the latest general headlines, use get_top_headlines.
- For news about a topic, use search_news_by_topic.
- If a user asks a follow-up like 'what about tomorrow there?', infer the city/topic from the conversation history.
- If weather fails because the location is missing, ask the user to provide a city.
- Keep answers clear and concise.
- Format weather and news in readable sections.
""".strip()


class LangChainWeatherNewsAgent:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.client = MCPToolClient(self.project_root)
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self._agent = self._build_agent()

    @property
    def is_configured(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    def _build_agent(self):
        if not self.is_configured:
            return None

        llm = ChatOpenAI(model=self.model_name, temperature=0)
        tools = self._build_tools()
        return create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)

    def _build_tools(self):
        client = self.client

        @tool
        def get_current_weather(city: str) -> str:
            """Get the current weather for a city. Input should be only the city or location name."""
            try:
                data = client.call_tool_sync(
                    "mcp_config/weather_server.py",
                    "get_current_weather",
                    {"city": city},
                )
                if not data.get("ok", True):
                    return f"Weather service error: {data.get('error', 'Unknown error')}"
                return (
                    f"Weather in {data['resolved_name']}\n"
                    f"Temperature: {data['temperature_c']}°C\n"
                    f"Condition: {data['condition']}\n"
                    f"Wind: {data['wind_speed_kmh']} km/h\n"
                    f"Time: {data['observed_at']}"
                )
            except MCPToolError as exc:
                return f"Weather service error: {exc}"

        @tool
        def get_tomorrow_weather(city: str) -> str:
            """Get tomorrow's weather forecast for a city. Input should be only the city or location name."""
            try:
                data = client.call_tool_sync(
                    "mcp_config/weather_server.py",
                    "get_weather_forecast",
                    {"city": city},
                )
                if not data.get("ok", True):
                    return f"Weather service error: {data.get('error', 'Unknown error')}"
                return (
                    f"Forecast for {data['resolved_name']} on {data['date']}\n"
                    f"Min / Max: {data['min_temp_c']}°C / {data['max_temp_c']}°C\n"
                    f"Rain probability: {data['rain_probability_percent']}%\n"
                    f"Expected condition: {data['condition']}"
                )
            except MCPToolError as exc:
                return f"Weather service error: {exc}"

        @tool
        def get_top_headlines(limit: int = 5) -> str:
            """Get the latest general news headlines. Use for requests like latest headlines, latest news, or what's new today."""
            try:
                data = client.call_tool_sync(
                    "mcp_config/news_server.py",
                    "get_top_headlines",
                    {"limit": limit},
                )
                if not data.get("ok", True):
                    return f"News service error: {data.get('error', 'Unknown error')}"
                articles = data.get("articles", [])
                if not articles:
                    return "No headlines found."

                lines = ["Latest headlines:"]
                for idx, article in enumerate(articles, start=1):
                    lines.append(
                        f"{idx}. {article.get('title', 'Untitled')}\n"
                        f"   Source: {article.get('source', 'Unknown source')}\n"
                        f"   URL: {article.get('url', '')}"
                    )
                return "\n".join(lines)
            except MCPToolError as exc:
                return f"News service error: {exc}"

        @tool
        def search_news_by_topic(topic: str, limit: int = 5) -> str:
            """Search recent news about a specific topic, company, person, technology, country, or event."""
            try:
                data = client.call_tool_sync(
                    "mcp_config/news_server.py",
                    "search_news",
                    {"topic": topic, "limit": limit},
                )
                if not data.get("ok", True):
                    return f"News service error: {data.get('error', 'Unknown error')}"
                articles = data.get("articles", [])
                if not articles:
                    return f"No matching articles found for topic: {topic}"

                lines = [f"News about {topic}:"]
                for idx, article in enumerate(articles, start=1):
                    summary = article.get("summary") or "No summary available."
                    lines.append(
                        f"{idx}. {article.get('title', 'Untitled')}\n"
                        f"   Source: {article.get('source', 'Unknown source')}\n"
                        f"   Summary: {summary}\n"
                        f"   URL: {article.get('url', '')}"
                    )
                return "\n".join(lines)
            except MCPToolError as exc:
                return f"News service error: {exc}"

        return [get_current_weather, get_tomorrow_weather, get_top_headlines, search_news_by_topic]

    def answer(self, messages: list[dict[str, str]]) -> str:
        if not self._agent:
            raise RuntimeError(
                "LangChain agent is not configured. Please set OPENAI_API_KEY to use the agent mode."
            )

        result: dict[str, Any] = self._agent.invoke({"messages": messages})
        response_messages = result.get("messages", [])
        if not response_messages:
            return "Sorry, I could not generate a response."

        last_message = response_messages[-1]
        content = getattr(last_message, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return "\n".join(part for part in text_parts if part).strip() or str(content)
        return str(content)