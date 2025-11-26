from fastapi import WebSocket
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        # Lista de processos/clientes conectados
        self.active_connections: List[WebSocket] = []
        
        # [SO - MEMÓRIA COMPARTILHADA]
        # Esta estrutura atua como uma tabela de alocação de recursos na RAM.
        # Chave: Recurso (Horário) -> Valor: Processo Dono (WebSocket)
        self.temporary_locks: Dict[str, WebSocket] = {} 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        """
        [SO - GARBAGE COLLECTION / PREVENÇÃO DE DEADLOCK]
        Quando um processo (cliente) morre ou desconecta, o sistema deve
        liberar os recursos que ele segurava para evitar inanição (Starvation).
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        locks_to_release = []
        # Varre a memória procurando locks órfãos deste socket
        for resource_id, owner_socket in list(self.temporary_locks.items()):
            if owner_socket == websocket:
                locks_to_release.append(resource_id)
                del self.temporary_locks[resource_id]
        
        # Avisa os outros processos que os recursos foram liberados
        for resource in locks_to_release:
            print(f"[SO - CLEANUP] Liberando lock abandonado: {resource}")
            await self.broadcast({
                "tipo": "desbloqueio_temporario",
                "recurso": resource,
                "status": "free"
            })

    async def broadcast(self, message: dict):
        """
        [SO - COMUNICAÇÃO INTER-PROCESSOS (IPC)]
        Envia uma mensagem para todos os processos conectados (Multicast).
        Usado para manter a consistência de estado visual entre clientes.
        """
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                await self.disconnect(connection)

    async def request_lock(self, websocket: WebSocket, resource_id: str):
        """
        [SO - SEMÁFORO LÓGICO]
        Tenta adquirir o acesso exclusivo a um recurso (horário).
        Se já estiver na tabela temporary_locks, nega o acesso (Busy Wait evitado).
        """
        if resource_id in self.temporary_locks:
            if self.temporary_locks[resource_id] != websocket:
                return False # Recurso Ocupado
        
        # Adquire o Lock na memória
        self.temporary_locks[resource_id] = websocket
        
        # Propaga o estado de bloqueio para todos (Sincronização)
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

    def consume_lock(self, resource_id: str):
        """
        [SO - TRANSIÇÃO DE ESTADO]
        Remove o lock da memória (Volátil) quando o dado é persistido no disco.
        Evita inconsistência entre o estado em RAM e o estado em Disco.
        """
        if resource_id in self.temporary_locks:
            del self.temporary_locks[resource_id]
            print(f"[SO - MEMORY] Lock temporário consumido (persistido): {resource_id}")

    async def force_release_resource(self, resource_prefix: str):
        # [SO - INTERRUPÇÃO] Força a liberação administrativa de um recurso
        locks_to_remove = [k for k in self.temporary_locks.keys() if k.startswith(f"{resource_prefix}|")]
        for key in locks_to_remove:
            del self.temporary_locks[key]

        await self.broadcast({
            "tipo": "recurso_removido",
            "id": resource_prefix
        })

manager = ConnectionManager()