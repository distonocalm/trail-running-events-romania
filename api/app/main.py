from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, scrape, sources

app = FastAPI(title="Trail Running Events Romania")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(scrape.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
