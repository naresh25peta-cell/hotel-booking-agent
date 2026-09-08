# Hotel Booking Agent

A multi-agent AI assistant that helps users search for hotels, check room availability, and complete bookings — including price calculation and (simulated) payment — through a conversational chat interface.

Built as a group project to practice production-style LLM application patterns: multi-agent orchestration, guardrails, observability, automated testing, and containerized deployment.

## What it does

- **Search & availability** — find hotels by location and check room availability for given dates.
- **Booking flow** — a multi-step conversation: price quote → payment → booking confirmation, with room type selection (Standard / Deluxe / Suite).
- **Guardrails** — input/output filtering to keep the assistant on-topic and safe.
- **Observability** — request tracing via Langfuse and experiment tracking via MLflow.
- **Auth** — JWT-based login (chat also works anonymously).

## Architecture

The core is a [LangGraph](https://github.com/langchain-ai/langgraph) state machine with an orchestrator that routes each user turn to the right specialist agent:

```
                 ┌──────────────┐
   user turn ──▶ │ Orchestrator │
                 └──────┬───────┘
                        │ routes by intent
          ┌─────────────┼─────────────────┐
          ▼                               ▼
┌───────────────────────┐      ┌────────────────────┐
│ Search & Availability  │      │   Booking Agent     │
│ Agent                  │      │ (price → payment →  │
│                        │      │  booking, looped)   │
└───────────┬────────────┘      └──────────┬──────────┘
            ▼                              ▼
   search_hotels,                 calculate_price,
   check_hotel_availability       process_payment,
   (tools)                        create_booking (tools)
```

Each agent's tool calls loop back through the graph until the turn resolves, so a booking can span multiple messages (e.g. "book the Deluxe room" → price shown → card details → confirmed).

## Tech stack

| Layer | Tools |
|---|---|
| Agents / orchestration | LangChain, LangGraph, Azure OpenAI |
| Backend API | FastAPI, SQLAlchemy, PostgreSQL / SQLite |
| Frontend | Streamlit |
| Auth | JWT (python-jose), passlib/bcrypt |
| Observability | Langfuse (tracing), MLflow (experiment tracking) |
| Testing | pytest, pytest-cov (unit + integration, CI-enforced coverage gate) |
| Infra | Docker / docker-compose, GitHub Actions CI, AWS CodePipeline + ECR |

## Project structure

```
backend/
  agents/         # orchestrator, search/availability, booking agents
  api/             # FastAPI app, routes, auth
  db/              # SQLAlchemy models, seed data
  evaluation/      # response/payment evaluators
  graph/           # LangGraph state graph definition
  guardrails/      # input/output/tool guardrails
  observability/   # tracing setup
  schemas/         # Pydantic schemas
  services/        # business logic (pricing, payment, availability, booking)
  tools/           # LangChain @tool wrappers around services
  utils/           # logging, langfuse compatibility shim
frontend/
  streamlit_app.py # chat UI
tests/
  unit/            # per-service/agent unit tests
  integration/      # end-to-end API/chat flow tests
```

## Getting started

**Prerequisites:** Python 3.11+, [uv](https://github.com/astral-sh/uv) (or pip), and an Azure OpenAI deployment.

1. Copy the environment template and fill in your credentials:
   ```
   cp .env.example .env   # if present — otherwise create .env with the keys backend/config.py expects
   ```
   Required: `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`.
   Optional: `DATABASE_URL` (defaults to local SQLite), `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`, `JWT_SECRET_KEY`.

2. Install dependencies:
   ```
   uv sync
   ```

3. Seed the database:
   ```
   uv run python -m backend.db.seed
   ```

4. Run the backend and frontend (two terminals):
   ```
   uv run uvicorn backend.api.main:app --reload
   uv run streamlit run frontend/streamlit_app.py
   ```

### Or with Docker

```
docker compose up --build
```
Runs the backend (`:8000`), frontend (`:8502`), and a pgAdmin instance (`:5050`).

## Testing

```
uv run pytest tests/unit/ tests/integration/ --cov=backend
```

CI (`.github/workflows/tests.yml`) runs unit + integration tests on every push and enforces a 60% coverage minimum.

## Deployment

`Dockerfile.backend` / `Dockerfile.frontend` build production images; `buildspec.yml` defines an AWS CodeBuild/CodePipeline job that builds, tags, and pushes the backend image to ECR.

## Contributors

Built as a team project by Naresh Kumar, Alaa Hamid, and Abrar.
