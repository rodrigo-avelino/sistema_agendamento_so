from fastapi import WebSocket
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.temporary_locks: Dict[str, WebSocket] = {} 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        locks_to_release = []
        for resource_id, owner_socket in list(self.temporary_locks.items()):
            if owner_socket == websocket:
                locks_to_release.append(resource_id)
                del self.temporary_locks[resource_id]
        
        for resource in locks_to_release:
            # Só avisa desbloqueio se realmente tiver algo para liberar
            print(f"[SO - CLEANUP] Liberando lock abandonado: {resource}")
            await self.broadcast({
                "tipo": "desbloqueio_temporario",
                "recurso": resource,
                "status": "free"
            })

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                await self.disconnect(connection)

    async def request_lock(self, websocket: WebSocket, resource_id: str):
        if resource_id in self.temporary_locks:
            if self.temporary_locks[resource_id] != websocket:
                return False 
        self.temporary_locks[resource_id] = websocket
        
        await self.broadcast({
            "tipo": "bloqueio_temporario",
            "recurso": resource_id,
            "dono_id": id(websocket)
        })
        return True

    async def release_lock(self, resource_id: str):
        if resource_id in self.temporary_locks:
            del self.temporary_locks[resource_id]
            await self.broadcast({
                "tipo": "desbloqueio_temporario",
                "recurso": resource_id
            })

    # [NOVO MÉTODO - CORREÇÃO DO BUG]
    def consume_lock(self, resource_id: str):
        """
        Remove o lock da memória SILENCIOSAMENTE.
        Usado quando o agendamento é confirmado no disco.
        Assim, o disconnect não vai disparar 'desbloqueio' depois.
        """
        if resource_id in self.temporary_locks:
            del self.temporary_locks[resource_id]
            print(f"[SO - MEMORY] Lock temporário consumido (persistido): {resource_id}")

    async def force_release_resource(self, resource_prefix: str):
        locks_to_remove = [k for k in self.temporary_locks.keys() if k.startswith(f"{resource_prefix}|")]
        for key in locks_to_remove:
            del self.temporary_locks[key]

        await self.broadcast({
            "tipo": "recurso_removido",
            "id": resource_prefix
        })

manager = ConnectionManager()