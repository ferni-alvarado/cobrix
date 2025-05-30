# endpoint HTTP que WhatsApp llama cuando recibís un mensaje.

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter()

VERIFY_TOKEN = "cobrix123"


@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado correctamente con Meta")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        print(f"❌ Token incorrecto: recibido='{token}', esperado='{VERIFY_TOKEN}'")
        return JSONResponse(status_code=403, content={"error": "Forbidden"})


@router.post("/webhook/whatsapp")
async def receive_whatsapp_message(request: Request):
    payload = await request.json()

    # Extraer datos
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    sender_wa_id = message["from"]
    text = message.get("text", {}).get("body", "")

    print(f"👤 Mensaje de {sender_wa_id}: {text}")

    # Por ahora solo logueamos. Más adelante: responder, enviar a agente, etc.
    return JSONResponse(content={"status": "received"})
