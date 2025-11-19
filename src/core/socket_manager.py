from fastapi import WebSocket
from typing import List, Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
        # Memória Compartilhada de Bloqueios Temporários
        # Chave: "medico_id|data_hora" -> Valor: WebSocket do cliente que bloqueou
        self.temporary_locks: Dict[str, WebSocket] = {} 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # [SO - RESOURCE CLEANUP]
        # Se o cliente desconectar (fechar aba), liberamos todos os bloqueios dele
        # para evitar Deadlock (recursos presos para sempre).
        locks_to_release = [k for k, v in self.temporary_locks.items() if v == websocket]
        for key in locks_to_release:
            del self.temporary_locks[key]
        return locks_to_release # Retorna o que foi liberado para avisar os outros

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    async def request_lock(self, websocket: WebSocket, resource_id: str):
        """
        Tenta adquirir o 'Semaforo' para um recurso específico.
        """
        # Verifica se já está bloqueado por OUTRA pessoa
        if resource_id in self.temporary_locks:
            if self.temporary_locks[resource_id] != websocket:
                return False # Falha: Recurso já em uso (Busy Wait simulado no front)
        
        # Adquire o bloqueio
        self.temporary_locks[resource_id] = websocket
        
        # Avisa TODO MUNDO que esse recurso agora está "Amarelo" (Em seleção)
        await self.broadcast({
            "tipo": "bloqueio_temporario",
            "recurso": resource_id,
            "status": "locked"
        })
        return True

    async def release_lock(self, resource_id: str):
        """Libera o recurso manualmente (usuário clicou em cancelar)"""
        if resource_id in self.temporary_locks:
            del self.temporary_locks[resource_id]
            
            # Avisa TODO MUNDO que o recurso está "Verde" (Livre) novamente
            await self.broadcast({
                "tipo": "desbloqueio_temporario",
                "recurso": resource_id,
                "status": "free"
            })

manager = ConnectionManager()