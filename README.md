
# Weather + News Streamlit App with MCP

A Python 3.10+ Streamlit application that answers user questions about:

- current weather conditions
- tomorrow’s weather forecast
- latest news headlines
- news about a specific topic

The project uses a **custom agent orchestrator** and **local MCP servers** to provide a consistent interface for external data sources.

---

## Architecture Overview

```text
User question
   ↓
Streamlit chat UI (app.py)
   ↓
Agent Orchestrator (agents/orchestrator.py)
   ├─ intent detection
   ├─ routing
   ├─ conversational context handling
   └─ response formatting
   ↓
MCP Client (agents/mcp_client.py)
   ├─ weather MCP server
   └─ news MCP server
```

---

## Project Structure

```text
project/
├── app.py
├── agents/
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
* Can be enabled only if a token is provided through an environment variable

---

## Design Choice

The assignment requires:

* MCP-based integration
* agent orchestration
* no required API keys

To satisfy these requirements:

* weather is handled through a dedicated MCP server connected to Open-Meteo
* news is handled through a dedicated MCP server connected to **Google News RSS by default**
* the application works **without any API keys**
* `THE_NEWS_API_TOKEN` is **optional** and is only used if you want to switch to TheNewsAPI later

---

## Features Implemented

* Natural language intent detection: weather / news / both
* Request routing through a custom orchestrator
* Multi-turn conversation support with simple memory
* Streamlit chat interface
* MCP server integration using Python MCP SDK
* Graceful error handling
* No required API keys

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

## Optional Environment Variable

This project does **not** require any API keys to run.

If you want to use **TheNewsAPI** instead of the default Google News RSS source, you may optionally set:

### macOS / Linux

```bash
export THE_NEWS_API_TOKEN="your_token_here"
streamlit run app.py
```

### Windows PowerShell

```powershell
$env:THE_NEWS_API_TOKEN="your_token_here"
streamlit run app.py
```

If this variable is not set, the application will continue to work using **Google News RSS**.

---

## Notes / Limitations

1. The default news provider is RSS-based, so summaries may be shorter or less structured than commercial news APIs.
2. Topic search works well for common queries, but may be less precise than paid news services.
3. Follow-up question handling is intentionally lightweight and based on simple conversational memory.
4. The project uses a **custom orchestrator** instead of an LLM-based agent so that it can run without model credentials or paid APIs.

---

## Suggested Demo Flow for Screencast

1. Open the Streamlit application
2. Ask for the current weather in a city
3. Ask a follow-up question about tomorrow’s forecast
4. Ask for the latest headlines
5. Ask for topic-based news
6. Ask a combined question with both weather and news


