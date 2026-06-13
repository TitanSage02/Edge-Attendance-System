from typing import Dict, Set, List, Any, Optional
from fastapi import WebSocket, Depends
from pydantic import BaseModel, ValidationError, Field
import json
import asyncio
from datetime import datetime
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.models.user import User
from app.models.log import Log
from app.services.log_service import db_logger
from app.api.v1.deps import get_db, get_current_user
from app.db.session import AsyncSessionLocal

class WebSocketMessage(BaseModel):
    channel: str = Field(..., min_length=1)
    data: dict = Field(default_factory=dict)
    timestamp: Optional[str] = None
    message_type: Optional[str] = None
    sequence_id: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConnectionManager:
    def __init__(self):
        # Websockets par canal
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "logs": set(),
            "presence": set(),
            "modules": set(),
            "alerts": set(),
            "all": set(),
        }
        # Stockage des derniers messages en mémoire
        self.message_history: Dict[str, List[Dict[str, Any]]] = {
            "logs": [],
            "presence": [],
            "modules": [],
            "alerts": [],
        }
        self.history_size = 100  # Nombre de messages à conserver par canal
        self.max_connections = 1000  # Limite globale de connexions
        self.max_connections_per_channel = 200  # Limite par canal
        self.connection_lock = asyncio.Lock()  # Verrou pour accès concurrents
        self._is_logging = False  # Flag pour éviter la récursion
        self.heartbeat_interval = 30  # Intervalle de heartbeat en secondes
        self.connection_timestamps: Dict[WebSocket, float] = {}  # Timestamps des dernières activités
        self.sequence_counters: Dict[str, int] = {  # Compteurs de séquence par canal
            "logs": 0,
            "presence": 0,
            "modules": 0,
            "alerts": 0,
        }

    async def connect(
        self,
        websocket: WebSocket,
        channel: str = "all",
        db: AsyncSession = None,
        user: User = None
    ) -> None:
        """Connecte un client à un canal spécifique."""
        try:
            await websocket.accept()
            self.connection_timestamps[websocket] = time.time()

            if channel not in self.active_connections:
                await db_logger.error(
                    f"❌ Tentative de connexion à un canal WebSocket inexistant: {channel} 🚨",
                    source="websocket_manager"
                )
                await websocket.close(code=1000, reason="Canal inexistant")
                return

            async with self.connection_lock:
                total_connections = sum(len(conns) for conns in self.active_connections.values())
                if total_connections >= self.max_connections:
                    await db_logger.warning(
                        "⚠️ Limite globale de connexions WebSocket atteinte 🔌",
                        source="websocket_manager"
                    )
                    await websocket.close(code=1000, reason="Trop de connexions globales")
                    return

                if len(self.active_connections[channel]) >= self.max_connections_per_channel:
                    await db_logger.warning(
                        f"Limite de connexions pour le canal {channel} atteinte",
                        source="websocket_manager"
                    )
                    await websocket.close(code=1000, reason=f"Trop de connexions pour le canal {channel}")
                    return

                self.active_connections[channel].add(websocket)

            client_ip = websocket.client.host if websocket.client else "unknown"
            if not self._is_logging:
                self._is_logging = True
                try:
                    await db_logger.debug(
                        f"Client connecté au canal {channel}",
                        source="websocket_manager",
                        user_id=user.id if user else None,
                        details={"client_ip": client_ip}
                    )
                finally:
                    self._is_logging = False

            # Démarrer le heartbeat pour cette connexion
            asyncio.create_task(self._start_heartbeat(websocket, channel))

            # Envoyer l'historique en mémoire
            await self._send_history(websocket, channel)

        except Exception as e:
            await db_logger.error(
                f"Erreur lors de la connexion WebSocket: {str(e)}",
                source="websocket_manager"
            )
            await websocket.close(code=1011, reason="Erreur interne du serveur")

    async def _start_heartbeat(self, websocket: WebSocket, channel: str) -> None:
        """Gère le heartbeat pour une connexion WebSocket."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                if websocket not in self.connection_timestamps:
                    break

                last_activity = self.connection_timestamps[websocket]
                if time.time() - last_activity > self.heartbeat_interval * 2:
                    await db_logger.warning(
                        f"Connexion inactive détectée sur le canal {channel}",
                        source="websocket_manager"
                    )
                    await self.disconnect(websocket, channel)
                    break

                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception:
                    await self.disconnect(websocket, channel)
                    break

        except Exception as e:
            await db_logger.error(
                f"Erreur dans le heartbeat: {str(e)}",
                source="websocket_manager"
            )
            await self.disconnect(websocket, channel)

    async def _send_history(self, websocket: WebSocket, channel: str) -> None:
        """Envoie l'historique des messages à un nouveau client."""
        try:
            if channel != "all":
                for message in self.message_history[channel]:
                    await websocket.send_json(message)
            else:
                all_history = []
                for chan in self.message_history:
                    all_history.extend(self.message_history[chan])
                
                all_history.sort(key=lambda x: x.get("timestamp", ""))
                
                for message in all_history[-self.history_size:]:
                    await websocket.send_json(message)
        except Exception as e:
            await db_logger.error(
                f"Erreur lors de l'envoi de l'historique: {str(e)}",
                source="websocket_manager"
            )

    async def broadcast(self, message: Dict[str, Any], channel: str) -> None:
        """Diffuse un message à tous les clients d'un canal spécifique."""
        message_type = message.get("type", "unknown")
        await db_logger.debug(
            f"Préparation de la diffusion d'un message de type '{message_type}' sur le canal '{channel}'. Tous les utilisateurs connectés à ce canal vont recevoir cette information en temps réel.",
            source="websocket_manager",
            channel=channel,
        )
        
        try:
            if channel == "all":
                raise ValueError("Diffusion directe sur le canal 'all' non autorisée")
        
            # Incrémenter le compteur de séquence pour ce canal
            self.sequence_counters[channel] = self.sequence_counters.get(channel, 0) + 1
            
            validated_message = WebSocketMessage(
                channel=channel,
                data=message,
                timestamp=datetime.now().isoformat(),
                sequence_id=self.sequence_counters[channel]
            )
            message_dict = validated_message.dict(exclude_none=True)
            
            await db_logger.debug(
                f"Message validé et préparé pour diffusion avec le numéro de séquence {self.sequence_counters[channel]}. Le système garantit ainsi l'ordre des messages pour les utilisateurs.",
                source="websocket_manager",
                event_type="message_validated",
                channel=channel,
                sequence_id=self.sequence_counters[channel]
            )
        
        except ValidationError as e:
            if not self._is_logging:
                self._is_logging = True
                try:
                    await db_logger.error(
                        f"Message WebSocket invalide pour le canal {channel}",
                        source="websocket_manager",
                        details={"erreur": str(e)}
                    )
                finally:
                    self._is_logging = False
            return
        
        except ValueError as e:
            if not self._is_logging:
                self._is_logging = True
                try:
                    # await db_logger.error(
                    #     f"Erreur de diffusion sur le canal {channel}",
                    #     source="websocket_manager",
                    #     details={"erreur": str(e)}
                    # )
                    pass
                finally:
                    self._is_logging = False
            return

        # Stocker en mémoire immédiatement pour la performance
        if channel in self.message_history:
            self.message_history[channel].append(message_dict)
            if len(self.message_history[channel]) > self.history_size:
                self.message_history[channel].pop(0)
            
            await db_logger.debug(
                f"Message archivé dans l'historique du canal '{channel}' (total: {len(self.message_history[channel])} messages). L'historique permet aux nouveaux utilisateurs de voir les événements récents.",
                source="websocket_manager",
                event_type="message_archived",
                channel=channel,
                history_size=len(self.message_history[channel])
            )

        # Diffuser aux clients
        await self._broadcast_to_clients(message_dict, channel)

    async def _broadcast_to_clients(self, message_dict: Dict[str, Any], channel: str) -> None:
        """Handle the actual broadcasting to websocket clients"""
        
        clients_on_channel = len(self.active_connections.get(channel, []))
        clients_on_all = len(self.active_connections.get("all", []))
        total_recipients = clients_on_channel + clients_on_all
        
        await db_logger.debug(
            f"Diffusion du message vers {total_recipients} utilisateurs connectés. Canal spécifique '{channel}': {clients_on_channel} utilisateurs, Canal général 'all': {clients_on_all} utilisateurs.",
            source="websocket_manager",
        )
        
        # Diffusion aux clients du canal spécifique
        if channel in self.active_connections:
            disconnected = set()
            if not self._is_logging:
                self._is_logging = True
                try:
                    await db_logger.debug(
                        f"Diffusion d'un message sur le canal {channel}",
                        source="websocket_manager",
                        details={"canal": channel, "nombre_clients": len(self.active_connections[channel])}
                    )
                finally:
                    self._is_logging = False

            async with self.connection_lock:
                clients_sent = 0
                for connection in self.active_connections[channel]:
                    try:
                        await connection.send_json(message_dict)
                        clients_sent += 1
                    except Exception as e:
                        if not self._is_logging:
                            self._is_logging = True
                            try:
                                await db_logger.error(
                                    f"Impossible d'envoyer le message à un utilisateur connecté sur le canal '{channel}'. La connexion de l'utilisateur semble avoir été interrompue. Erreur: {str(e)}",
                                    source="websocket_manager",                               
                                    error_details=str(e),
                                    client_ip=connection.client.host if connection.client else "unknown"
                                )
                            finally:
                                self._is_logging = False
                        disconnected.add(connection)

                # Supprimer les connexions en erreur
                for conn in disconnected:
                    self.active_connections[channel].discard(conn)
                
                if clients_sent > 0:
                    result_msg = f"Message diffusé avec succès à {clients_sent} utilisateur(s) connecté(s) au canal '{channel}'."
                else:
                    result_msg = f"Aucun utilisateur connecté au canal '{channel}' pour recevoir le message."
                
                if len(disconnected) > 0:
                    result_msg += f" {len(disconnected)} connexion(s) fermée(s) détectée(s) et nettoyée(s)."
                
                await db_logger.debug(
                    result_msg,
                    source="websocket_manager",
                    details={"canal": channel, "clients_envoyes": clients_sent, "clients_deconnectes": len(disconnected)}
                )

        # Diffusion aux clients du canal "all"
        message_with_channel = {**message_dict, "channel": channel}
        
        disconnected = set()
        clients_all_sent = 0
        
        async with self.connection_lock:
            for connection in self.active_connections["all"]:
                try:
                    await connection.send_json(message_with_channel)
                    clients_all_sent += 1
                except Exception as e:
                    if not self._is_logging:
                        self._is_logging = True
                        try:
                            await db_logger.debug(
                                f"Erreur lors de l'envoi au client sur le canal 'all'",
                                source="websocket_manager",
                                details={"erreur": str(e), "client_ip": connection.client.host if connection.client else "unknown"}
                            )
                        finally:
                            self._is_logging = False
                    disconnected.add(connection)

            # Supprimer les connexions en erreur
            for conn in disconnected:
                self.active_connections["all"].discard(conn)
                
            await db_logger.debug(
                f"🔊 Message envoyé à {clients_all_sent} clients sur canal 'all' ✅",
                source="websocket_manager",
                details={"canal": channel, "clients_all_envoyes": clients_all_sent, "clients_all_deconnectes": len(disconnected)}
            )

    async def disconnect(self, websocket: WebSocket, channel: str = None) -> None:
        """Déconnecte un client d'un canal spécifique ou de tous les canaux."""
        async with self.connection_lock:
            client_ip = websocket.client.host if websocket.client else "unknown"
            
            # Supprimer le timestamp de connexion
            self.connection_timestamps.pop(websocket, None)
            
            if channel:
                if channel in self.active_connections:
                    self.active_connections[channel].discard(websocket)
                    await db_logger.debug(
                        f"Client déconnecté du canal {channel}",
                        source="websocket_manager",
                        details={"client_ip": client_ip}
                    )
            else:
                for chan in self.active_connections:
                    self.active_connections[chan].discard(websocket)
                await db_logger.debug(
                    "Client déconnecté de tous les canaux",
                    source="websocket_manager",
                    details={"client_ip": client_ip}
                )

            try:
                await websocket.close()
            except Exception as e:
                await db_logger.debug(
                    f"Erreur lors de la fermeture de la connexion: {str(e)}",
                    source="websocket_manager"
                )

# Create a singleton instance
ws_manager = ConnectionManager()