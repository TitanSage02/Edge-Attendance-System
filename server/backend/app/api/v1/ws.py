from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Union

import json
from datetime import datetime

from app.core.websocket_manager import ws_manager

from app.models.user import User
from app.models.api_key import ApiKey
from app.services.log_service import db_logger

from app.api.v1.deps import get_db, get_current_user_ws, get_api_key
from app.services.mqtt_service import mqtt_client

from app.models.module import Module 

router = APIRouter()

VALID_CHANNELS = ["all", "logs", "presence", "modules", "alerts"]

async def get_websocket_auth(websocket: WebSocket) -> Union[User, None]:
    """Authenticate WebSocket connection using token query parameter."""
    return await get_current_user_ws(websocket)

@router.websocket("/")
async def websocket_endpoint(
    websocket: WebSocket, 
    channel: str = Query("all"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time events.
    
    Args:
        websocket: WebSocket connection
        channel: Event channel to subscribe to (all, logs, presence, modules, alerts)
        db: Database session for command processing
    
    Supported Commands:
    - ping: Test connection, returns pong with timestamp
    - restart_module: Restart a module by ID (requires module_uid in payload)
    
    Example Command:
    ```json
    {"command": "ping"}
    {"command": "restart", "module_uid": "module123"}
    ```
    
    Note: WebSocket connections must use WSS (secure WebSocket) with TLS.
    """
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    # Log connection attempt
    db_logger.debug(f"Nouvelle tentative de connexion WebSocket depuis {client_info} pour surveiller le canal '{channel}'. L'utilisateur souhaite recevoir les mises à jour en temps réel.")
    
    # Authenticate the connection
    auth = await get_websocket_auth(websocket)
    
    # Reject unauthorized connections
    if not auth:
        db_logger.warning(f"Connexion WebSocket refusée pour {client_info}. L'utilisateur n'a pas fourni d'authentification valide pour accéder aux données temps réel.")
        await websocket.close(code=1008)  # Policy violation
        return
    
    # Validate channel
    if channel not in VALID_CHANNELS:
        db_logger.warning(f"Canal WebSocket invalide demandé: '{channel}' par {client_info}. Les canaux autorisés sont: {', '.join(VALID_CHANNELS)}")
        await websocket.close(code=1008)  # Policy violation
        return
    
    # Log successful authentication
    auth_id = getattr(auth, 'id', 'unknown')
    db_logger.debug(f"Connexion WebSocket établie avec succès pour l'utilisateur #{auth_id} depuis {client_info}. L'utilisateur recevra maintenant les mises à jour en temps réel du canal '{channel}'.")
    
    # Connect to the requested channel
    await ws_manager.connect(websocket, channel)
    
    # Log successful connection
    db_logger.debug(f"🔗 WebSocket connecté au channel '{channel}': user_id={auth_id}, client={client_info}")
    
    await db_logger.debug(
        "🔌 Connexion WebSocket authentifiée établie avec succès ✅",
        user_id=auth_id
    )
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                # Process client commands if authenticated
                message = json.loads(data)
                command = message.get("command")
                
                if command == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif command == "restart_module":
                    module_uid = message.get("module_uid")
                    if not module_uid:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Le module_uid est requis"
                        })
                        continue
                    
                    # Validate module existence
                    query = select(Module).filter(Module.uid == module_uid)
                    result = await db.execute(query)
                    
                    module = result.scalar_one_or_none()
                    if not module:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Le module_uid est requis"
                        })
                        continue
                    
                    # Publish command to MQTT
                    mqtt_client.publish(
                        f"command/{module_uid}/restart",
                        payload={"command": "restart", "module_uid": module_uid}
                    )
                    
                    await websocket.send_json({
                        "type": "success",
                        "message": f"Restart command sent to module {module_uid}"
                    }) 

                    await db_logger.debug(
                        "🔄 Commande WebSocket traitée avec succès ✅",
                        command=command,
                        module_uid=module_uid,
                        auth_id=auth_id,
                        client=client_info,
                        source="ws_api"
                    )
                
                elif command:
                    await db_logger.warning(
                        "❓ Commande WebSocket inconnue reçue ⚠️",
                        command=command,
                        auth_id=auth_id,
                        client=client_info,
                        source="ws_api"
                    )
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown command: {command}"
                    })
            except json.JSONDecodeError:
                await db_logger.warning(
                    f"⚠️ JSON invalide reçu via WebSocket, client: {client_info} 📄",
                    source="ws_api"
                )
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                await db_logger.error(
                    f"❌ Erreur lors de l'exécution de commande WebSocket: {str(e)}, client: {client_info} 🚨",
                    source="ws_api"
                )

                await websocket.send_json({
                    "type": "error",
                    "message": f"Command error: {str(e)}"
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)
        await db_logger.debug(
            "🔌 Connexion WebSocket fermée proprement ✅",
            channel=channel,
            auth_id=auth_id,
            client=client_info,
            source="ws_api"
        )
    except Exception as e:
        await db_logger.error(
            "❌ Erreur WebSocket critique détectée 🚨",
            error=str(e),
            channel=channel,
            auth_id=auth_id,
            client=client_info,
            source="ws_api"
        )
        
        ws_manager.disconnect(websocket, channel)

# Channel-specific WebSocket endpoints
@router.websocket("/logs")
async def websocket_logs(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for log events."""
    # Manually set channel and call main endpoint logic
    channel = "logs"
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    # Authenticate the connection
    auth = await get_websocket_auth(websocket)
    
    # Reject unauthorized connections
    if not auth:
        db_logger.warning(f"🚫 Tentative de connexion WebSocket non autorisée: {client_info} ⚠️")
        await websocket.close(code=1008)
        return
    
    # Validate channel
    if channel not in VALID_CHANNELS:
        db_logger.warning(f"⚠️ Canal invalide: {channel}, client: {client_info} 🔍")
        await websocket.close(code=1008)
        return
    
    # Connect to WebSocket manager
    await ws_manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping commands for channel-specific endpoints
            try:
                message = json.loads(data)
                if message.get("command") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)

@router.websocket("/presence")
async def websocket_presence(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for presence events."""
    # Manually set channel and call main endpoint logic
    channel = "presence"
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    # Authenticate the connection
    auth = await get_websocket_auth(websocket)
    
    # Reject unauthorized connections
    if not auth:
        db_logger.warning(f"🚫 Tentative de connexion WebSocket non autorisée: {client_info} ⚠️")
        await websocket.close(code=1008)
        return
    
    # Connect to WebSocket manager
    await ws_manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping commands for channel-specific endpoints
            try:
                message = json.loads(data)
                if message.get("command") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)

@router.websocket("/modules")
async def websocket_modules(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for module status events."""
    # Manually set channel and call main endpoint logic
    channel = "modules"
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    # Authenticate the connection
    auth = await get_websocket_auth(websocket)
    
    # Reject unauthorized connections
    if not auth:
        db_logger.warning(f"🚫 Tentative de connexion WebSocket non autorisée: {client_info} ⚠️")
        await websocket.close(code=1008)
        return
    
    # Connect to WebSocket manager
    await ws_manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping commands for channel-specific endpoints
            try:
                message = json.loads(data)
                if message.get("command") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)

@router.websocket("/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for alert events."""
    # Manually set channel and call main endpoint logic
    channel = "alerts"
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    # Authenticate the connection
    auth = await get_websocket_auth(websocket)
    
    # Reject unauthorized connections
    if not auth:
        db_logger.warning(f"🚫 Tentative de connexion WebSocket non autorisée: {client_info} ⚠️")
        await websocket.close(code=1008)
        return
    
    # Connect to WebSocket manager
    await ws_manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping commands for channel-specific endpoints
            try:
                message = json.loads(data)
                if message.get("command") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
            except:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)