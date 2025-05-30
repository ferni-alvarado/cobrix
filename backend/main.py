from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import webhook_mercado_pago, webhook_whatsapp, websocket
from backend.tests import whatsapp_test

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


app.include_router(webhook_mercado_pago.router)
app.include_router(websocket.router)
app.include_router(webhook_whatsapp.router)
app.include_router(whatsapp_test.router)
