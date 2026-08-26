# FIND-engine

FIND-engine is a high-performance search aggregator designed to query multiple search engines and platforms concurrently, normalize their metadata schemas, eliminate duplicate links, and present them in a premium, glassmorphic user interface.

```
                  Search Query
                       │
                       ▼
               Search Orchestrator
             /    /    │    \    \
            /    /     │     \    \
           ▼    ▼      ▼      ▼    ▼
          WP   HN    arXiv   DDG  [G/B]*
           │    │      │      │    │
           └────┴──┬───┴──────┴────┘
                   ▼
              Raw Results
                   │
                   ▼
         Normalization & Parsing
                   │
                   ▼
          URL Deduplication
                   │
                   ▼
            Ranking & Boost
                   │
                   ▼
           React UI Frontend
```
*\*G/B represent Google and Bing (optional keyed providers)*

---

## Key Features

1. **Concurrent Search Orchestration**: Utilizes Python's `asyncio` and `httpx` to trigger search queries to Wikipedia, Hacker News, arXiv, and DuckDuckGo in parallel.
2. **Schema Normalization**: Maps diverse metadata from different platforms (Atom XML feeds, JSON hits, raw HTML tables) into a single, unified `SearchResult` schema.
3. **Smart URL Deduplication**: Standardizes URLs by stripping protocols, `www.`, trailing slashes, and analytics tracker parameters (UTM codes). Merges duplicate links into a single card showing badges for all sourcing engines.
4. **Weighted Ranking & Boosting**: Automatically boosts search results returned by multiple engines to prioritize common hits.
5. **Premium Glassmorphic UI**: High-fidelity dark mode interface built with React, styled using fluid typography, micro-interactions, loading skeletons, and interactive brand-colored filter chips.

---

## Technical Stack

- **Backend**: FastAPI (Python 3.13), `httpx` (async HTTP queries), `BeautifulSoup` (HTML parser), Pydantic (data validation).
- **Frontend**: React (Vite template), Vanilla CSS (glassmorphism/containment layouts), `lucide-react` (SVG icons).
- **Containerization**: Docker, Docker Compose.

---

## System Schema

### SearchResult Model (Pydantic / Pydantic BaseModel)

```python
class SearchResult(BaseModel):
    title: str
    url: str
    domain: str                           # Extracted root domain name
    snippet: str                          # Standardized text description/abstract
    source: str                           # Comma-separated sources (e.g. "wikipedia, hackernews")
    published_date: Optional[str] = None  # ISO format date or relative string
    raw_score: Optional[float] = 0.0      # Normalised relevance score
```

### Endpoints

- **`GET /health`**: Standard application status check.
  - *Response*: `{"status": "healthy"}`
- **`GET /search?q={query_string}`**: Queries all engines, dedupes results, and returns an interleaved list.
  - *Response*:
    ```json
    {
      "results": [
        {
          "title": "Quantum computing - Wikipedia",
          "url": "https://en.wikipedia.org/?curid=24609",
          "domain": "wikipedia.org",
          "snippet": "Quantum computing is a rapidly-emerging technology that harnesses...",
          "source": "wikipedia, duckduckgo",
          "published_date": "2026-08-25T13:42:00Z",
          "raw_score": 10.0
        }
      ]
    }
    ```

---

## Installation & Local Startup

### 1. Backend Server

Navigate to the `backend/` folder and install dependencies:
```bash
pip install -r backend/requirements.txt
```

Create a `.env` file inside `backend/` to configure optional keyed search providers (Google, Bing):
```env
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX=your_google_custom_search_engine_id
BING_API_KEY=your_bing_api_key
```
*If keys are omitted, the engine runs in keyless mode using Wikipedia, Hacker News, arXiv, and DuckDuckGo.*

Start the FastAPI development server:
```bash
python main.py
```
The backend API will be available at `http://localhost:8000`. You can inspect interactive documentation at `http://localhost:8000/docs`.

### 2. Frontend App

Navigate to the `frontend/` folder and install packages:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
```
The React UI will run at `http://localhost:5173`.

---

## Containerization (Docker)

To launch the aggregated services in a containerized environment, use Docker Compose:

```bash
docker-compose up --build
```

The system will spin up:
- The FastAPI backend at `http://localhost:8000`
- The React frontend (served via Nginx) at `http://localhost:80`