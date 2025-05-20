import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.websocket_manager import connect, disconnect

router = APIRouter()


@router.get("/ws-test")
async def test_websocket():
    """Endpoint para probar si la ruta del WebSocket está funcionando"""
    return {
        "status": "ok",
        "message": "WebSocket route is working. Connect to /ws with a WebSocket client.",
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Nueva conexión WebSocket recibida")
    await connect(websocket)
    try:
        while True:
            # Esperar mensajes del cliente
            data = await websocket.receive_text()
            print(f"Mensaje recibido del cliente: {data}")

            # Enviar un eco como respuesta (opcional)
            await websocket.send_text(
                json.dumps({"event": "echo", "message": f"Echo: {data}"})
            )
    except WebSocketDisconnect:
        print("Cliente desconectado")
        await disconnect(websocket)
    except Exception as e:
        print(f"Error en la conexión WebSocket: {e}")
        await disconnect(websocket)
