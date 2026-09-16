from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ALLOWED_ORIGINS
from .routers import events, organizers, orders, payments, scan

app = FastAPI(title="billetterie — API publique")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(scan.router)
app.include_router(organizers.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
