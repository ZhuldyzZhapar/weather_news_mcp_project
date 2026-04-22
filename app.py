from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from agents.langchain_agent import LangChainWeatherNewsAgent
from agents.orchestrator import WeatherNewsOrchestrator


PROJECT_ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="Weather + News MCP Agent", page_icon="🌦️", layout="centered")
st.title("🌦️ Weather + News MCP Agent")
st.caption("Ask about current weather, tomorrow's forecast, latest headlines, or news on a topic.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I can answer things like:\n"
                "- What's the weather in Almaty?\n"
                "- Will it rain tomorrow in London?\n"
                "- What are the latest headlines?\n"
                "- News about AI and the weather in Astana"
            ),
        }
    ]

if "langchain_agent" not in st.session_state:
    st.session_state.langchain_agent = LangChainWeatherNewsAgent(PROJECT_ROOT)

if "fallback_orchestrator" not in st.session_state:
    st.session_state.fallback_orchestrator = WeatherNewsOrchestrator(PROJECT_ROOT)

use_agent = st.session_state.langchain_agent.is_configured

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Type your question here...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if use_agent:
                    history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages
                    ]
                    answer = st.session_state.langchain_agent.answer(history)
                else:
                    fallback = st.session_state.fallback_orchestrator.answer(prompt)
                    answer = (
                        "_Fallback mode: OPENAI_API_KEY not set, so the app is using the custom orchestrator._\n\n"
                        + fallback.text
                    )

                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as exc:
                error_message = (
                    "Sorry, something went wrong while contacting the agent tools. "
                    f"Details: {exc}"
                )
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

with st.sidebar:
    st.subheader("Mode")
    if use_agent:
        st.success(
            f"LangChain agent mode is active. Model: {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}"
        )
    else:
        st.warning("OPENAI_API_KEY is not set. Running in fallback custom-orchestrator mode.")

    st.subheader("What this app does")
    st.write("- Uses LangChain agent orchestration when an OpenAI API key is available")
    st.write("- Falls back to a custom orchestrator if no LLM key is configured")
    st.write("- Calls local MCP servers for weather and news")
    st.write("- Supports multi-turn chat through conversation history")
    st.write("- Runs without requiring any API key for weather/news data sources")