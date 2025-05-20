import json

from fastapi import WebSocket

clients = set()


async def connect(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    # Enviar mensaje de confirmación al cliente
    await websocket.send_text(
        json.dumps(
            {
                "event": "connection_established",
                "message": "Conectado al servidor de notificaciones",
            }
        )
    )
    print(f"Cliente WebSocket conectado. Total de clientes: {len(clients)}")


async def disconnect(websocket: WebSocket):
    if websocket in clients:
        clients.remove(websocket)
    print(f"Cliente WebSocket desconectado. Total de clientes: {len(clients)}")


async def broadcast_payment_update(data: dict):
    if not clients:
        print("No hay clientes conectados para recibir la actualización de pago")
        return

    print(f"Enviando actualización de pago a {len(clients)} clientes")
    disconnected = set()
    for client in clients:
        try:
            await client.send_text(json.dumps(data))
        except Exception as e:
            print(f"Error al enviar a cliente: {e}")
            disconnected.add(client)
    clients.difference_update(disconnected)
