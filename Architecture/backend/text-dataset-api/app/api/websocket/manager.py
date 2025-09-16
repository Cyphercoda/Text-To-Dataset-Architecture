"""
WebSocket connection manager for real-time updates
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for a single user or resource"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, metadata: Optional[Dict[str, Any]] = None):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        if metadata:
            self.metadata[websocket] = metadata
        logger.debug(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.metadata:
            del self.metadata[websocket]
        logger.debug(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections"""
        disconnected = []
        for connection in self.active_connections:
            try:
                if connection.application_state == WebSocketState.CONNECTED:
                    await connection.send_text(message)
                else:
                    disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


class WebSocketManager:
    """Main WebSocket manager for all connections"""
    
    def __init__(self):
        # User connections: user_id -> ConnectionManager
        self.user_connections: Dict[str, ConnectionManager] = {}
        
        # Room connections: room_id -> ConnectionManager
        self.room_connections: Dict[str, ConnectionManager] = {}
        
        # Job connections: job_id -> ConnectionManager
        self.job_connections: Dict[str, ConnectionManager] = {}
        
        # Chat session connections: session_id -> ConnectionManager
        self.chat_connections: Dict[str, ConnectionManager] = {}
        
        # Connection to user mapping for cleanup
        self.connection_users: Dict[WebSocket, str] = {}
        
        # Heartbeat tasks
        self.heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}
    
    async def connect_user(
        self, 
        websocket: WebSocket, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Connect user WebSocket"""
        if user_id not in self.user_connections:
            self.user_connections[user_id] = ConnectionManager()
        
        await self.user_connections[user_id].connect(websocket, metadata)
        self.connection_users[websocket] = user_id
        
        # Start heartbeat for this connection
        self.heartbeat_tasks[websocket] = asyncio.create_task(
            self._heartbeat(websocket)
        )
        
        # Send connection confirmation
        await self.send_to_user(user_id, {
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect_user(self, websocket: WebSocket):
        """Disconnect user WebSocket"""
        if websocket in self.connection_users:
            user_id = self.connection_users[websocket]
            
            # Cancel heartbeat task
            if websocket in self.heartbeat_tasks:
                self.heartbeat_tasks[websocket].cancel()
                del self.heartbeat_tasks[websocket]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].disconnect(websocket)
                
                # Remove manager if no more connections
                if not self.user_connections[user_id].active_connections:
                    del self.user_connections[user_id]
            
            # Clean up mapping
            del self.connection_users[websocket]
            
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        for task in self.heartbeat_tasks.values():
            task.cancel()
        
        self.user_connections.clear()
        self.room_connections.clear()
        self.job_connections.clear()
        self.chat_connections.clear()
        self.connection_users.clear()
        self.heartbeat_tasks.clear()
        
        logger.info("All WebSocket connections disconnected")
    
    async def send_to_user(self, user_id: str, data: Dict[str, Any]):
        """Send message to specific user"""
        if user_id in self.user_connections:
            message = json.dumps(data)
            await self.user_connections[user_id].broadcast(message)
    
    async def send_to_users(self, user_ids: List[str], data: Dict[str, Any]):
        """Send message to multiple users"""
        message = json.dumps(data)
        for user_id in user_ids:
            if user_id in self.user_connections:
                await self.user_connections[user_id].broadcast(message)
    
    async def broadcast_to_all(self, data: Dict[str, Any]):
        """Broadcast message to all connected users"""
        message = json.dumps(data)
        for manager in self.user_connections.values():
            await manager.broadcast(message)
    
    # Job-specific methods
    async def subscribe_to_job(self, websocket: WebSocket, job_id: str):
        """Subscribe to job updates"""
        if job_id not in self.job_connections:
            self.job_connections[job_id] = ConnectionManager()
        
        await self.job_connections[job_id].connect(websocket)
        logger.debug(f"WebSocket subscribed to job {job_id}")
    
    async def send_job_update(self, job_id: str, data: Dict[str, Any]):
        """Send job update to subscribers"""
        if job_id in self.job_connections:
            message = json.dumps({
                "type": "job_update",
                "job_id": job_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            await self.job_connections[job_id].broadcast(message)
    
    # Chat-specific methods
    async def subscribe_to_chat(self, websocket: WebSocket, session_id: str):
        """Subscribe to chat session updates"""
        if session_id not in self.chat_connections:
            self.chat_connections[session_id] = ConnectionManager()
        
        await self.chat_connections[session_id].connect(websocket)
        logger.debug(f"WebSocket subscribed to chat session {session_id}")
    
    async def send_chat_message(self, session_id: str, data: Dict[str, Any]):
        """Send chat message to session participants"""
        if session_id in self.chat_connections:
            message = json.dumps({
                "type": "chat_message",
                "session_id": session_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            await self.chat_connections[session_id].broadcast(message)
    
    async def send_typing_indicator(self, session_id: str, user_id: str, is_typing: bool):
        """Send typing indicator to chat session"""
        if session_id in self.chat_connections:
            message = json.dumps({
                "type": "typing_indicator",
                "session_id": session_id,
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            })
            await self.chat_connections[session_id].broadcast(message)
    
    # Room-specific methods (for group features)
    async def join_room(self, websocket: WebSocket, room_id: str):
        """Join a room"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = ConnectionManager()
        
        await self.room_connections[room_id].connect(websocket)
        logger.debug(f"WebSocket joined room {room_id}")
    
    async def leave_room(self, websocket: WebSocket, room_id: str):
        """Leave a room"""
        if room_id in self.room_connections:
            self.room_connections[room_id].disconnect(websocket)
            
            # Remove room if empty
            if not self.room_connections[room_id].active_connections:
                del self.room_connections[room_id]
        
        logger.debug(f"WebSocket left room {room_id}")
    
    async def send_to_room(self, room_id: str, data: Dict[str, Any]):
        """Send message to all connections in a room"""
        if room_id in self.room_connections:
            message = json.dumps(data)
            await self.room_connections[room_id].broadcast(message)
    
    # Notification methods
    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to user"""
        await self.send_to_user(user_id, {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Processing updates
    async def send_processing_update(
        self, 
        user_id: str, 
        job_id: str, 
        status: str, 
        progress: float,
        message: Optional[str] = None
    ):
        """Send processing status update to user"""
        update_data = {
            "type": "processing_update",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to user
        await self.send_to_user(user_id, update_data)
        
        # Also send to job subscribers
        await self.send_job_update(job_id, {
            "status": status,
            "progress": progress,
            "message": message
        })
    
    # Analytics events
    async def send_analytics_event(self, user_id: str, event: Dict[str, Any]):
        """Send analytics event to user"""
        await self.send_to_user(user_id, {
            "type": "analytics_event",
            "data": event,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # System messages
    async def send_system_message(self, user_id: str, message: str, level: str = "info"):
        """Send system message to user"""
        await self.send_to_user(user_id, {
            "type": "system_message",
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_system_message(self, message: str, level: str = "info"):
        """Broadcast system message to all users"""
        await self.broadcast_to_all({
            "type": "system_message",
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Heartbeat mechanism
    async def _heartbeat(self, websocket: WebSocket, interval: int = 30):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while websocket.application_state == WebSocketState.CONNECTED:
                await asyncio.sleep(interval)
                
                if websocket.application_state == WebSocketState.CONNECTED:
                    try:
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Heartbeat failed: {e}")
                        break
                else:
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
    
    # Statistics
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_users": len(self.user_connections),
            "total_connections": sum(
                len(manager.active_connections) 
                for manager in self.user_connections.values()
            ),
            "total_rooms": len(self.room_connections),
            "active_jobs": len(self.job_connections),
            "active_chats": len(self.chat_connections)
        }
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        if user_id in self.user_connections:
            return len(self.user_connections[user_id].active_connections)
        return 0
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has active WebSocket connection"""
        return user_id in self.user_connections and \
               len(self.user_connections[user_id].active_connections) > 0


# Global WebSocket manager instance
websocket_manager = WebSocketManager()