from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.websocket_manager import connect, disconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await disconnect(websocket)
