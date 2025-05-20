from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import webhook, websocket

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Backend API está funcionando correctamente"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Mercado Pago Integration"}


app.include_router(webhook.router)
app.include_router(websocket.router)
