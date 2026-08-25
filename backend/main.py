from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from orchestrator import SearchOrchestrator

app = FastAPI(
    title="FIND-engine API",
    description="Search aggregator backend querying Wikipedia, Hacker News, and arXiv.",
    version="1.0.0"
)

# Enable CORS for frontend requests (local development and dockerized environments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = SearchOrchestrator()

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

@app.get("/search")
async def search(q: str = Query(..., description="The search query string")) -> Dict[str, Any]:
    results = await orchestrator.search(q)
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    # Allow running directly using: python main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
