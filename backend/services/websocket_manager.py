import json

from fastapi import WebSocket

clients = set()


async def connect(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)


async def disconnect(websocket: WebSocket):
    clients.remove(websocket)


async def broadcast_payment_update(data: dict):
    disconnected = set()
    for client in clients:
        try:
            await client.send_text(json.dumps(data))
        except Exception:
            disconnected.add(client)
    clients.difference_update(disconnected)
