import asyncio
import datetime
import json
import os
from datetime import datetime

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI()

clients = set()


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Receives webhook notifications from Mercado Pago and prints the raw request body.
    """
    payload = await request.json()
    print("📩 Webhook received:")
    print(json.dumps(payload, indent=2))

    # Opcional: guardar el payload recibido en un archivo
    save_raw_webhook(payload)

    return JSONResponse(content={"message": "Webhook received successfully."})


def save_raw_webhook(payload: dict):
    """
    Saves the raw webhook payload to a JSON file for inspection.
    """
    os.makedirs("data/webhooks", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/webhooks/webhook_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"💾 Webhook saved to {filename}")


async def broadcast_payment_update(
    preference_id: str, payment_status: str, order_id: str = None
):
    """
    Sends a payment update to all connected WebSocket clients.
    """
    message = {
        "event": "payment_update",
        "preference_id": preference_id,
        "payment_status": payment_status,
        "order_id": order_id,
    }

    disconnected_clients = set()
    for client in clients:
        try:
            await client.send_text(json.dumps(message))
        except WebSocketDisconnect:
            disconnected_clients.add(client)

    clients.difference_update(disconnected_clients)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the frontend to receive real-time updates.
    """
    await websocket.accept()
    clients.add(websocket)
    print("✅ WebSocket client connected")

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("❌ WebSocket client disconnected")
        clients.remove(websocket)
