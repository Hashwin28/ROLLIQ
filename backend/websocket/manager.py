"""
ROLLIQ WebSocket Connection Manager.
Handles real-time sensor streaming, posture alerts, and movement event broadcasting.
"""
from typing import Dict, List, Set, Any, Optional
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("rolliq.websocket")


class ConnectionManager:
    """
    Manages active WebSocket connections grouped by session_id.
    Broadcasts real-time events to connected clients.
    """

    def __init__(self):
        # session_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global listeners (e.g. dashboard overview)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, session_id: Optional[str] = None):
        """Accept connection and register under session_id or globally."""
        await websocket.accept()
        if session_id:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(websocket)
        else:
            self.global_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: Optional[str] = None):
        """Remove connection."""
        if session_id and session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        self.global_connections.discard(websocket)

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send JSON payload to all clients listening to a specific session."""
        targets = set()
        if session_id in self.active_connections:
            targets.update(self.active_connections[session_id])
        targets.update(self.global_connections)

        if not targets:
            return

        payload = json.dumps(message)
        dead = []
        for connection in targets:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)

        # Clean up any broken connections
        for dead_conn in dead:
            self.disconnect(dead_conn, session_id)

    async def broadcast_sensor_data(self, session_id: str, readings: List[Dict[str, Any]]):
        await self.broadcast_to_session(
            session_id,
            {
                "type": "sensor_data",
                "session_id": session_id,
                "readings": readings,
            },
        )

    async def broadcast_posture(self, session_id: str, posture: str, confidence: float):
        await self.broadcast_to_session(
            session_id,
            {
                "type": "posture_update",
                "session_id": session_id,
                "posture": posture,
                "confidence": confidence,
            },
        )

    async def broadcast_movement(self, session_id: str, movement: Dict[str, Any]):
        await self.broadcast_to_session(
            session_id,
            {
                "type": "movement_event",
                "session_id": session_id,
                "movement": movement,
            },
        )

    async def broadcast_alert(self, session_id: str, alert: Dict[str, Any]):
        await self.broadcast_to_session(
            session_id,
            {
                "type": "alert",
                "session_id": session_id,
                "alert": alert,
            },
        )


ws_manager = ConnectionManager()
