# Weather + News Streamlit App with MCP

A Python 3.10+ Streamlit application that answers user questions about:

- current weather conditions
- tomorrow’s weather forecast
- latest news headlines
- news about a specific topic

The project combines:

- **Streamlit** for the chat interface
- **LangChain agent orchestration** for tool-based reasoning
- **local MCP servers** for weather and news access
- **fallback custom orchestration** when no LLM API key is provided

---

## Project Goal

The goal of this project is to build a conversational application that can answer questions about weather and news using external data sources through **MCP (Model Context Protocol)**.

The application supports:

- weather-related questions
- news-related questions
- combined questions about both weather and news
- simple follow-up questions in a multi-turn conversation

---

## Architecture Overview

```text
User question
   ↓
Streamlit chat UI (app.py)
   ↓
Application Router
   ├─ LangChain Agent Mode (if OPENAI_API_KEY is set)
   │    ├─ LangChain agent
   │    ├─ tool selection
   │    ├─ conversational context
   │    └─ final response generation
   │
   └─ Fallback Custom Orchestrator Mode
        ├─ intent detection
        ├─ routing
        ├─ simple memory
        └─ response formatting
   ↓
MCP Client (agents/mcp_client.py)
   ├─ weather MCP server
   └─ news MCP server
```

---

## How It Works

### 1. User asks a question

The user enters a natural language query in the Streamlit interface.

Examples:

* `What's the weather in Almaty?`
* `Will it rain tomorrow in London?`
* `What are the latest headlines?`
* `News about AI`
* `What's the weather in Astana and latest news about space?`

### 2. The app chooses the orchestration mode

The app supports two execution modes:

#### LangChain Agent Mode

If `OPENAI_API_KEY` is provided, the application uses a **LangChain agent** with tool calling.

The agent:

* interprets the user’s request
* decides whether to call the weather tool, the news tool, or both
* uses chat history for follow-up questions
* generates the final natural language response

#### Fallback Custom Mode

If no `OPENAI_API_KEY` is provided, the application falls back to a custom non-LLM orchestrator.

This mode:

* detects weather/news intent using rules
* routes requests manually
* keeps basic conversation context
* allows the project to run without paid model access

---

## Project Structure

```text
project/
├── app.py
├── agents/
│   ├── langchain_agent.py
│   ├── mcp_client.py
│   ├── orchestrator.py
│   └── parser.py
├── mcp_config/
│   ├── news_server.py
│   └── weather_server.py
├── requirements.txt
├── README.md
└── video_link.txt
```

---

## Main Components

### `app.py`

The Streamlit entry point.
Responsible for:

* rendering the chat interface
* storing chat history
* choosing agent mode or fallback mode
* displaying answers and errors

### `agents/langchain_agent.py`

Implements the LangChain-based agent flow.

Responsibilities:

* initialize the LLM
* define tool wrappers for weather and news
* pass conversation history to the agent
* let the agent decide which tool(s) to call
* return the final answer

### `agents/orchestrator.py`

Fallback custom orchestrator.

Responsibilities:

* parse query intent
* route to weather, news, or both
* combine results
* support basic follow-up logic

### `agents/parser.py`

Contains rule-based parsing logic for:

* weather intent
* news intent
* topic extraction
* simple location handling
* follow-up interpretation in fallback mode

### `agents/mcp_client.py`

Client layer for interacting with MCP servers.

Responsibilities:

* call weather tools
* call news tools
* normalize tool responses
* isolate app logic from server implementation details

### `mcp_config/weather_server.py`

Local MCP server for weather data.

Uses:

* Open-Meteo Geocoding API
* Open-Meteo Forecast API

### `mcp_config/news_server.py`

Local MCP server for news data.

Uses:

* Google News RSS by default
* optional TheNewsAPI integration if a token is provided

---

## Data Sources

### Weather

* **Open-Meteo Geocoding API**
* **Open-Meteo Forecast API**
* No API key required

### News

Default mode:

* **Google News RSS**
* No API key required

Optional mode:

* **TheNewsAPI**
* Used only if `THE_NEWS_API_TOKEN` is provided

---

## MCP Design

This project uses local MCP servers to standardize access to external tools.

Benefits of this approach:

* clear separation between app logic and data access
* easier tool reuse
* cleaner orchestration layer
* consistent interface for both weather and news functionality

In this project:

* the weather MCP server exposes weather-related functions
* the news MCP server exposes headline and topic-search functions
* the Streamlit application interacts with these servers through a dedicated MCP client layer

---

## LangChain Design

LangChain is used in **agent mode** to provide tool-based orchestration.

The LangChain agent is responsible for:

* understanding the user’s intent
* deciding which tool(s) to call
* combining results from multiple tools
* handling follow-up conversation context
* generating a final user-friendly answer

This makes the app closer to a real conversational assistant compared to pure rule-based routing.

---

## Features Implemented

* Natural language support for weather and news questions
* Current weather lookup
* Tomorrow weather forecast
* Latest headlines
* News by topic
* Combined weather + news questions
* Multi-turn chat interface
* LangChain-based tool-calling agent mode
* Fallback custom orchestration mode
* MCP integration for external data access
* Graceful error handling
* No required API keys for the default version

---

## Example Questions

* `What's the weather in Almaty?`
* `Will it rain tomorrow in London?`
* `What are the latest headlines?`
* `News about AI`
* `What's the weather in Astana and latest news about space?`
* `What about tomorrow there?`

---

## Setup Instructions

### 1. Create and activate a virtual environment

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The application usually opens in the browser at:

* `http://localhost:8501`

---

## Environment Variables

### Optional: OpenAI API key for LangChain agent mode

If you provide an OpenAI API key, the application will run in **LangChain Agent Mode**.

#### macOS / Linux

```bash
export OPENAI_API_KEY="your_key_here"
streamlit run app.py
```

#### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="your_key_here"
streamlit run app.py
```

If `OPENAI_API_KEY` is not set, the application will still work in **Fallback Custom Mode**.

---

### Optional: TheNewsAPI token

If you want to use TheNewsAPI instead of the default Google News RSS source, you may also set:

#### macOS / Linux

```bash
export THE_NEWS_API_TOKEN="your_token_here"
streamlit run app.py
```

#### Windows PowerShell

```powershell
$env:THE_NEWS_API_TOKEN="your_token_here"
streamlit run app.py
```

If this variable is not set, the application continues to work using **Google News RSS**.

---

## Execution Modes

### Mode 1 — LangChain Agent Mode

Used when:

* `OPENAI_API_KEY` is available

Advantages:

* better understanding of natural language
* better handling of combined questions
* more flexible follow-up interaction
* tool-based reasoning with an LLM

### Mode 2 — Fallback Custom Mode

Used when:

* no LLM API key is available

Advantages:

* runs without paid model access
* still supports the main project requirements
* keeps the application usable in restricted environments

---

## Notes / Limitations

1. The default news provider is RSS-based, so summaries may be shorter or less structured than commercial news APIs.
2. Topic-based news search works well for common queries, but may be less precise than premium news providers.
3. The fallback mode uses lightweight rule-based parsing, so it is less flexible than the LangChain agent mode.
4. Some complex date expressions may require clearer phrasing.
5. OpenAI-based LangChain mode requires separate API billing and is not included in ChatGPT subscription plans.

---

## Suggested Demo Flow for Screencast

1. Open the Streamlit application
2. Show the initial interface
3. Ask for the current weather in a city
4. Ask a follow-up about tomorrow
5. Ask for the latest headlines
6. Ask for topic-based news
7. Ask a combined question with both weather and news
8. Show that the application can run with MCP-based tools

---

## Submission Notes

Before submission:

1. Make sure all project files are included
2. Add your real public screencast URL into `video_link.txt`
3. Zip the project folder
4. Rename the archive according to the required format

Example:

```text
Module Name_PT1_FirstName_LastName.zip
```

---

## Summary

This project demonstrates:

* Streamlit-based conversational UI
* MCP-based tool integration
* weather and news external data access
* LangChain agent orchestration
* fallback custom orchestration without LLM dependency
* multi-turn interaction and practical error handling
