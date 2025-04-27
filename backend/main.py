from fastapi import FastAPI

from backend.api import webhook, websocket

app = FastAPI()

app.include_router(webhook.router)
app.include_router(websocket.router)
