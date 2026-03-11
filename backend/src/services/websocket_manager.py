"""WebSocket connection manager for real-time alerts."""
from typing import Dict, List, Set
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasting logic."""

    def __init__(self):
        # Maps channel name (e.g., "portfolio_123", "system") to a set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps a WebSocket to the set of channels it is subscribed to mapping
        self.connection_channels: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, channels: List[str] = None):
        """Accept a websocket connection and subscribe it to specified channels."""
        await websocket.accept()
        channels = channels or ["system"]
        
        self.connection_channels[websocket] = set(channels)
        
        for channel in channels:
            if channel not in self.active_connections:
                self.active_connections[channel] = set()
            self.active_connections[channel].add(websocket)
            
        logger.info(f"Client connected. Subscribed to channels: {channels}")

    def disconnect(self, websocket: WebSocket):
        """Remove a websocket connection and clean up its subscriptions."""
        channels = self.connection_channels.pop(websocket, set())
        
        for channel in channels:
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]
                    
        logger.info(f"Client disconnected from channels: {list(channels)}")

    async def broadcast_alert(self, alert_data: dict, channel: str = "system"):
        """Broadcast a message to all clients subscribed to a specific channel."""
        connections = self.active_connections.get(channel, set())
        if not connections:
            logger.debug(f"No active subscribers for channel: {channel}")
            return
            
        logger.info(f"Broadcasting alert to {len(connections)} clients on channel '{channel}'")
        
        # Create a list of currently active connections to iterate over safely
        for connection in list(connections):
            try:
                await connection.send_json(alert_data)
            except Exception as e:
                logger.warning(f"Failed to send message to client. Disconnecting. Error: {e}")
                self.disconnect(connection)


# Global singleton instance
manager = ConnectionManager()
