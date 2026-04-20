from __future__ import annotations

from pathlib import Path

import streamlit as st

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

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = WeatherNewsOrchestrator(PROJECT_ROOT)

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
                response = st.session_state.orchestrator.answer(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as exc:
                error_message = (
                    "Sorry, something went wrong while contacting the agent tools. "
                    f"Details: {exc}"
                )
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

with st.sidebar:
    st.subheader("What this app does")
    st.write("- Uses a custom orchestrator to detect weather, news, or mixed intent")
    st.write("- Calls local MCP servers for weather and news")
    st.write("- Remembers the previous city/topic for simple follow-up questions")
    st.write("- Runs without requiring any API key by default")
