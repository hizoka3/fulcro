from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, carta, chat, ingest

app = FastAPI(title="Defensor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, tags=["ingest"])
app.include_router(alerts.router, tags=["alerts"])
app.include_router(carta.router, tags=["carta"])
app.include_router(chat.router, tags=["chat"])


@app.get("/health")
def health():
    return {"ok": True, "version": "0.1.0"}
