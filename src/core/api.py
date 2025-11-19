from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List
from src.storage import JsonStorage
from src.core.socket_manager import manager # <--- Importa nosso gerenciador
import json

api_router = APIRouter(prefix="/api")

db_medicos = JsonStorage('medicos.json')
db_consultas = JsonStorage('consultas.json')

class AgendamentoRequest(BaseModel):
    paciente_nome: str
    medico_id: int
    data_hora: str 

# --- 1. Endpoint do WebSocket (Conexão Real-Time) ---
@api_router.websocket("/ws")
@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Aguarda mensagens do Frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Formato esperado da chave do recurso: "ID_MEDICO|DATA_HORA"
            # Ex: "1|2025-11-20T14:00:00"
            
            if message['acao'] == 'selecionar':
                # Cliente quer pegar o "semáforo"
                recurso_id = f"{message['medico_id']}|{message['data_hora']}"
                sucesso = await manager.request_lock(websocket, recurso_id)
                
                # Responde apenas para quem pediu, dizendo se conseguiu ou não
                await websocket.send_json({
                    "tipo": "resposta_selecao",
                    "sucesso": sucesso,
                    "recurso": recurso_id
                })

            elif message['acao'] == 'cancelar_selecao':
                # Cliente desistiu, libera o semáforo
                recurso_id = f"{message['medico_id']}|{message['data_hora']}"
                await manager.release_lock(recurso_id)

    except WebSocketDisconnect:
        # [SO - TOLERÂNCIA A FALHAS]
        # Se a conexão cair, o manager limpa os locks e avisa o resto da rede
        liberados = manager.disconnect(websocket)
        for recurso in liberados:
            await manager.broadcast({
                "tipo": "desbloqueio_temporario",
                "recurso": recurso,
                "status": "free"
            })

# --- 2. Endpoints HTTP (CRUD) ---
@api_router.get("/medicos")
def listar_medicos():
    return db_medicos.read()

@api_router.get("/consultas")
def listar_consultas():
    return db_consultas.read()

@api_router.post("/agendar")
async def criar_agendamento(agendamento: AgendamentoRequest): # Note o 'async' aqui agora
    """
    Cria agendamento e avisa todo mundo em tempo real.
    """
    consultas_existentes = db_consultas.read()
    
    # Verificação de Conflito
    for consulta in consultas_existentes:
        if (consulta['medico_id'] == agendamento.medico_id and 
            consulta['data_hora'] == agendamento.data_hora):
            raise HTTPException(status_code=409, detail="Horário já ocupado!")

    novo_agendamento = {
        "paciente": agendamento.paciente_nome,
        "medico_id": agendamento.medico_id,
        "data_hora": agendamento.data_hora,
        "status": "confirmado"
    }
    
    # 1. Persistência (Disco/Lock)
    db_consultas.add(novo_agendamento)
    
    # 2. Notificação Real-Time (WebSocket)
    # Avisa todos os fronts para pintarem esse horário de vermelho IMEDIATAMENTE
    await manager.broadcast({
        "tipo": "novo_agendamento",
        "dados": novo_agendamento
    })
    
    return {"msg": "Agendado com sucesso"}