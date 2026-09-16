from fastapi import FastAPI

from .routers import events, orders, payments, scan

app = FastAPI(title="billetterie — API publique")

app.include_router(events.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(scan.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
