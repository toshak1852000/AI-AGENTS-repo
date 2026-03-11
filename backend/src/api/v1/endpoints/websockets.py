"""WebSocket endpoints for real-time alerts."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
import logging
from typing import Optional

from src.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/alerts")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Authentication token"),
    channel: Optional[str] = Query("system", description="Channel to subscribe to (e.g., system, portfolio_xyz)")
):
    """
    WebSocket endpoint for real-time alerts.
    Requires authentication via token query parameter.
    """
    # Note: In a real production app, validate the JWT token here
    # against the auth service. For now, we do a simple check.
    if not token:
        # We must accept or close the connection properly.
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket connection rejected: Missing token")
        return
        
    # Basic dummy validation logic (replace with actual JWT decoding)
    if token == "invalid_token":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket connection rejected: Invalid token")
        return

    # Accept the connection and subscribe to the requested channel
    channels = [channel] if channel else ["system"]
    await manager.connect(websocket, channels)

    try:
        while True:
            # Wait for any messages from the client (e.g., ping/keep-alive)
            data = await websocket.receive_text()
            logger.debug(f"Received message from WS client: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from channel(s) {channels}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
