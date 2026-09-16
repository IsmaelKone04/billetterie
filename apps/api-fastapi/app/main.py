from fastapi import FastAPI

from .routers import events

app = FastAPI(title="billetterie — API publique")

app.include_router(events.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
