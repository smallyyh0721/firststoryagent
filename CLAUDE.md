# CLAUDE.md — Story Agent

## Project Overview

Story Agent is an AI-powered story writer with Notion integration. It uses ZhipuAI's GLM-4.7 LLM to generate creative stories and stores them in a Notion database. The project has a Python/FastAPI backend and a vanilla JavaScript frontend.

## Repository Structure

```
backend/
  main.py              # FastAPI app entry point, lifespan management, CORS config
  api/
    stories.py          # REST endpoints for story CRUD + generation
  core/
    llm/
      client.py         # ZhipuAI GLM-4.7 client (OpenAI-compatible API)
      prompts.py         # Genre-specific story generation prompts
    notion/
      client.py          # Notion API wrapper — full CRUD for stories
      manager.py         # Singleton NotionClientManager with retry/backoff
  models/
    story.py             # Pydantic models: Story, Genre, Status enums, request/response schemas
frontend/
  index.html             # Single-page app shell (Generate, List, About pages)
  app.js                 # UI logic, API calls via Fetch, state management
  styles.css             # CSS with custom properties theming
```

## Tech Stack

- **Backend:** Python 3.8+, FastAPI, Uvicorn, Pydantic v2
- **Frontend:** Vanilla HTML/CSS/JS (ES6+, no build step)
- **LLM:** ZhipuAI GLM-4.7 via OpenAI-compatible HTTP API (httpx)
- **Storage:** Notion API (notion-client 2.2.1)
- **Testing:** pytest
- **Config:** python-dotenv, `.env` file

## Getting Started

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in NOTION_TOKEN, NOTION_DATABASE_ID, ZHIPUAI_API_KEY
```

## Common Commands

```bash
# Run backend server (from project root)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run backend directly
cd backend && python main.py

# Run tests
pytest

# Serve frontend (separate terminal)
python -m http.server 3000 --directory frontend
```

## API Endpoints

All story endpoints are under `/api/stories`:

| Method | Path                      | Description              |
|--------|---------------------------|--------------------------|
| POST   | `/api/stories/generate`   | Generate a new story     |
| GET    | `/api/stories`            | List stories (filterable)|
| GET    | `/api/stories/{story_id}` | Get a single story       |
| PUT    | `/api/stories/{story_id}` | Update a story           |
| DELETE | `/api/stories/{story_id}` | Archive/delete a story   |

Additional routes: `GET /` (info), `GET /health` (health check), `GET /docs` (Swagger UI).

## Environment Variables

Defined in `.env` (see `.env.example`):

| Variable             | Description                        |
|----------------------|------------------------------------|
| `NOTION_TOKEN`       | Notion integration token           |
| `NOTION_DATABASE_ID` | Target Notion database ID          |
| `ZHIPUAI_API_KEY`    | ZhipuAI API key for GLM-4.7       |

**Never commit `.env` or real credentials.**

## Architecture & Patterns

- **Dependency injection:** FastAPI `Depends()` provides LLM and Notion clients to route handlers.
- **Lifespan management:** Clients are initialized at startup and cleaned up at shutdown via `@asynccontextmanager` in `main.py`.
- **Singleton pattern:** `NotionClientManager` ensures a single Notion client instance.
- **Retry with backoff:** Notion operations retry up to 3 times with exponential backoff (1s, 2s, 4s) on transient errors.
- **Request logging:** Each story generation request gets a unique timestamp-based ID for log tracing.

## Data Models

**Genre enum:** Fantasy, Sci-Fi, Romance, Mystery, Horror, Adventure, Drama, Comedy, Thriller, Other

**Status enum:** Draft, In Progress, Completed, Published

**Story lengths:** short (~500 words), medium (~1500 words), long (~3000 words)

## Notion Database Schema

The Notion database expects these properties:
- **Title** (title) — story title
- **Genre** (multi_select) — story genre
- **Status** (select) — optional, defaults to Draft
- **CreatedAt** (date) — optional
- **WordCount** (number) — optional
- Story content is stored as paragraph blocks in the page body.

## Conventions for AI Assistants

- The backend uses **Pydantic v2** — use `model_validate()` not `parse_obj()`, `model_dump()` not `dict()`.
- Genre values must match the `Genre` enum in `backend/models/story.py`. The frontend maps genre strings to these enum values.
- The frontend hardcodes `http://localhost:8000` as the API base URL in `app.js`.
- No linter, formatter, or CI pipeline is configured. Keep code style consistent with existing files.
- Logging uses Python's `logging` module with `INFO` level by default.
- Error handling follows the pattern: catch specific exceptions (ValueError, KeyError) before generic Exception, and return appropriate HTTP status codes.
- The Notion client handles missing optional properties gracefully — do not assume all database properties exist.
