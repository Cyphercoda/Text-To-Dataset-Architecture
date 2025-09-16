"""
WebSocket routes for real-time communication
"""

import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import security_manager
from app.api.websocket.manager import websocket_manager
from app.services.auth.auth_service import auth_service

logger = logging.getLogger(__name__)

websocket_router = APIRouter()


async def verify_websocket_token(token: str, db: AsyncSession) -> Optional[str]:
    """Verify WebSocket authentication token"""
    try:
        payload = security_manager.decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Verify user exists and is active
        user = await auth_service.get_user_by_id(db, UUID(user_id))
        if not user or not user.is_active:
            return None
        
        return str(user.id)
    
    except Exception as e:
        logger.error(f"WebSocket token verification failed: {e}")
        return None


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Main WebSocket endpoint for real-time updates
    
    Connection URL: ws://localhost:8000/ws?token=<jwt_token>
    
    Message Types:
    - connection: Connection status updates
    - heartbeat: Keep-alive messages
    - processing_update: Document processing updates
    - chat_message: Chat messages
    - notification: System notifications
    - analytics_event: Analytics updates
    - system_message: System-wide messages
    """
    user_id = None
    
    try:
        # Verify authentication
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        user_id = await verify_websocket_token(token, db)
        if not user_id:
            await websocket.close(code=4002, reason="Invalid authentication token")
            return
        
        # Connect user
        await websocket_manager.connect_user(
            websocket=websocket,
            user_id=user_id,
            metadata={
                "connected_at": json.dumps({"timestamp": "now"}),
                "client_info": {
                    "headers": dict(websocket.headers),
                    "client": str(websocket.client) if websocket.client else None
                }
            }
        )
        
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process message based on type
                message_type = data.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                
                elif message_type == "subscribe":
                    # Subscribe to specific updates
                    await handle_subscription(websocket, user_id, data)
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from updates
                    await handle_unsubscription(websocket, user_id, data)
                
                elif message_type == "chat_message":
                    # Handle chat messages
                    await handle_chat_message(websocket, user_id, data, db)
                
                elif message_type == "typing_indicator":
                    # Handle typing indicators
                    await handle_typing_indicator(websocket, user_id, data)
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Message processing failed"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    
    finally:
        # Clean up connection
        if user_id:
            websocket_manager.disconnect_user(websocket)
            logger.info(f"WebSocket connection closed for user {user_id}")


async def handle_subscription(websocket: WebSocket, user_id: str, data: dict):
    """Handle subscription requests"""
    subscription_type = data.get("subscription_type")
    target_id = data.get("target_id")
    
    if not subscription_type or not target_id:
        await websocket.send_json({
            "type": "error",
            "message": "Missing subscription_type or target_id"
        })
        return
    
    if subscription_type == "job":
        # Subscribe to job updates
        await websocket_manager.subscribe_to_job(websocket, target_id)
        await websocket.send_json({
            "type": "subscription_confirmed",
            "subscription_type": "job",
            "target_id": target_id
        })
    
    elif subscription_type == "chat":
        # Subscribe to chat session
        await websocket_manager.subscribe_to_chat(websocket, target_id)
        await websocket.send_json({
            "type": "subscription_confirmed",
            "subscription_type": "chat",
            "target_id": target_id
        })
    
    elif subscription_type == "room":
        # Join a room
        await websocket_manager.join_room(websocket, target_id)
        await websocket.send_json({
            "type": "subscription_confirmed",
            "subscription_type": "room",
            "target_id": target_id
        })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown subscription type: {subscription_type}"
        })


async def handle_unsubscription(websocket: WebSocket, user_id: str, data: dict):
    """Handle unsubscription requests"""
    subscription_type = data.get("subscription_type")
    target_id = data.get("target_id")
    
    if not subscription_type or not target_id:
        await websocket.send_json({
            "type": "error",
            "message": "Missing subscription_type or target_id"
        })
        return
    
    if subscription_type == "room":
        # Leave room
        await websocket_manager.leave_room(websocket, target_id)
        await websocket.send_json({
            "type": "unsubscription_confirmed",
            "subscription_type": "room",
            "target_id": target_id
        })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Cannot unsubscribe from {subscription_type}"
        })


async def handle_chat_message(
    websocket: WebSocket, 
    user_id: str, 
    data: dict,
    db: AsyncSession
):
    """Handle incoming chat messages"""
    session_id = data.get("session_id")
    message_content = data.get("content")
    
    if not session_id or not message_content:
        await websocket.send_json({
            "type": "error",
            "message": "Missing session_id or content"
        })
        return
    
    # Process chat message (implementation would go to chat service)
    # For now, broadcast to chat session
    await websocket_manager.send_chat_message(session_id, {
        "user_id": user_id,
        "content": message_content,
        "timestamp": "now"
    })
    
    await websocket.send_json({
        "type": "message_sent",
        "session_id": session_id
    })


async def handle_typing_indicator(websocket: WebSocket, user_id: str, data: dict):
    """Handle typing indicators"""
    session_id = data.get("session_id")
    is_typing = data.get("is_typing", False)
    
    if not session_id:
        await websocket.send_json({
            "type": "error",
            "message": "Missing session_id"
        })
        return
    
    # Broadcast typing indicator
    await websocket_manager.send_typing_indicator(session_id, user_id, is_typing)


@websocket_router.websocket("/ws/admin")
async def admin_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin WebSocket endpoint for system monitoring
    
    Connection URL: ws://localhost:8000/ws/admin?token=<admin_jwt_token>
    """
    try:
        # Verify admin authentication
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        user_id = await verify_websocket_token(token, db)
        if not user_id:
            await websocket.close(code=4002, reason="Invalid authentication token")
            return
        
        # Verify admin role
        user = await auth_service.get_user_by_id(db, UUID(user_id))
        if not user or user.role != "admin":
            await websocket.close(code=4003, reason="Admin access required")
            return
        
        # Accept connection
        await websocket.accept()
        logger.info(f"Admin WebSocket connection established for user {user_id}")
        
        # Send initial stats
        await websocket.send_json({
            "type": "connection_stats",
            "data": websocket_manager.get_connection_stats()
        })
        
        # Handle admin commands
        while True:
            try:
                data = await websocket.receive_json()
                command = data.get("command")
                
                if command == "get_stats":
                    # Send connection statistics
                    await websocket.send_json({
                        "type": "connection_stats",
                        "data": websocket_manager.get_connection_stats()
                    })
                
                elif command == "broadcast_message":
                    # Broadcast system message
                    message = data.get("message", "")
                    level = data.get("level", "info")
                    await websocket_manager.broadcast_system_message(message, level)
                    
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "broadcast_message",
                        "success": True
                    })
                
                elif command == "disconnect_user":
                    # Disconnect specific user
                    target_user_id = data.get("user_id")
                    if target_user_id and target_user_id in websocket_manager.user_connections:
                        # Implementation for disconnecting user
                        await websocket.send_json({
                            "type": "command_result",
                            "command": "disconnect_user",
                            "success": True
                        })
                    else:
                        await websocket.send_json({
                            "type": "command_result",
                            "command": "disconnect_user",
                            "success": False,
                            "error": "User not connected"
                        })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown command: {command}"
                    })
            
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"Admin WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"Admin WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
    
    finally:
        logger.info("Admin WebSocket connection closed")


@websocket_router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status"""
    stats = websocket_manager.get_connection_stats()
    return {
        "status": "operational",
        "stats": stats
    }