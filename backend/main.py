from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

from orchestrator import SearchOrchestrator

app = FastAPI(
    title="FIND-engine API",
    description="Metasearch engine querying Wikipedia, Hacker News, arXiv, DuckDuckGo, Google, Bing, and Yahoo.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = SearchOrchestrator()

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

@app.get("/search")
async def search(
    q: str = Query(..., description="The search query string"),
    category: Optional[str] = Query(None, description="Optional category bias (e.g. tech, academic, news)")
) -> Dict[str, Any]:
    results = await orchestrator.search(q, category=category)
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
