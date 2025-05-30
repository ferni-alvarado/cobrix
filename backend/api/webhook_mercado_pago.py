from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.services.mercado_pago_service import process_webhook_event

router = APIRouter()


@router.post("/webhook")
async def webhook_handler(request: Request):
    try:
        # Try to get JSON body first
        try:
            payload = await request.json()
        except Exception:
            # If JSON parsing fails, check for query parameters
            payload = dict(request.query_params)
            if not payload:
                return JSONResponse(
                    content={"status": "error", "message": "No payload provided"},
                    status_code=400,
                )

        print(f"Webhook received: {payload}")
        await process_webhook_event(payload)
        return JSONResponse(content={"status": "received"}, status_code=200)
    except Exception as e:
        print(f"Error in webhook handler: {e}")
        # Return 200 even on error to prevent Mercado Pago from retrying
        # (You might want to log this error for debugging)
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=200
        )
