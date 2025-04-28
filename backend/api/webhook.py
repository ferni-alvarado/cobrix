from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.services.mercado_pago_service import process_webhook_event

router = APIRouter()


@router.post("/webhook")
async def webhook_handler(request: Request):
    payload = await request.json()
    await process_webhook_event(payload)
    return JSONResponse(content={"status": "received"}, status_code=200)
