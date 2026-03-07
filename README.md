# AgentScout

AI-powered LinkedIn post discovery and comment generation. Finds posts where people describe problems your product solves, analyses them, and generates tailored engagement comments via a Writer → Critic → Judge debate loop.

---

## Quick Start (Docker)

**Prerequisites:** Docker + Docker Compose, an Apify account, and Azure OpenAI access.

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials (see below)
```

### 2. Run

```bash
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:3000      |
| Backend API | http://localhost:8000   |
| API docs | http://localhost:8000/docs |

The database migrations run automatically on startup.

---

## Environment Variables (`backend/.env`)

| Variable | Description |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | API version (e.g. `2024-10-21`) |
| `GPT_MODEL` | Model for writing (e.g. `gpt-5.1-chat`) |
| `DEEPSEEK_MODEL` | Model for reasoning (e.g. `deepseek-r1`) |
| `APIFY_API_TOKEN` | Apify token for LinkedIn scraping |
| `DATABASE_URL` | PostgreSQL async URL |
| `DATABASE_URL_SYNC` | PostgreSQL sync URL (used by Alembic) |

---

## Pipeline Inputs

Go to **Pipeline** in the sidebar and fill in:

| Field | Required | Description |
|---|---|---|
| **Problem Description** | Yes | The pain point your product targets. Be specific. Min 10 chars. |
| **Product Description** | No | What your product does. Helps the AI write better comments. |
| **Queries** | No | Number of search queries to generate (default: 5) |
| **Posts / Query** | No | Max posts to scrape per query (default: 5) |
| **Min Relevance** | No | Minimum score (0–1) for a post to proceed to comment generation (default: 0.5). Use 0.4–0.5 for broader results. |
| **Platform** | No | Scraping platform (default: `linkedin`) |

**Example:**
- Problem: *"People frustrated by slow, inaccurate voice typing that doesn't work across all apps"*
- Product: *"Voice-to-text tool that works in any app with Fn key trigger, low latency"*
- Queries: `5`, Posts/Query: `5`, Min Relevance: `0.5`

---

## What Happens

1. **Query Generation** — DeepSeek-R1 generates `N` LinkedIn search queries from your problem description
2. **Scraping** — Apify scrapes LinkedIn posts matching those queries
3. **Analysis** — DeepSeek-R1 scores each post for relevance and opportunity
4. **Debate** — Posts above `min_relevance` go through Writer → Critic → Judge rounds to produce polished comments
5. **Persistence** — Everything saved to PostgreSQL, linked to the pipeline run

Results are visible under **Posts** and **Run History** in the sidebar.

---

## Stack

- **Backend:** FastAPI · Python 3.12 · SQLAlchemy 2 async · Alembic · PostgreSQL 16
- **AI:** Azure OpenAI (GPT for writing, DeepSeek-R1 for reasoning)
- **Scraping:** Apify — `apimaestro~linkedin-posts-search-scraper-no-cookies`
- **Frontend:** React 18 · TypeScript · Vite · Tailwind CSS 4
# AgentScout
