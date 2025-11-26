from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List
import json

from src.storage import JsonStorage
from src.core.socket_manager import manager
from src.core.logger import log_evento 

api_router = APIRouter(prefix="/api")

db_medicos = JsonStorage('consultas/medicos.json')
db_consultas = JsonStorage('consultas/consultas.json')

class AgendamentoRequest(BaseModel):
    paciente_nome: str
    medico_id: int
    data_hora: str 

class CancelamentoRequest(BaseModel):
    medico_id: int
    data_hora: str

# --- WebSocket ---
@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                acao = message.get('acao')

                # Força tudo para string
                m_id = str(message.get('medico_id', ''))
                d_hora = str(message.get('data_hora', ''))
                recurso_id = f"{m_id}|{d_hora}"

                if acao == 'selecionar':
                    if not m_id or not d_hora: continue
                    sucesso = await manager.request_lock(websocket, recurso_id)
                    
                    await websocket.send_json({
                        "tipo": "resposta_selecao",
                        "sucesso": sucesso,
                        "recurso": recurso_id,
                        "dados_originais": {
                            "medico_id": m_id,
                            "data_hora": d_hora
                        }
                    })

                elif acao == 'cancelar_selecao':
                    if m_id and d_hora:
                        await manager.release_lock(recurso_id)

            except json.JSONDecodeError:
                print("[WS ERROR] JSON inválido")
            except Exception as e:
                print(f"[WS ERROR] Erro: {e}")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)

# --- API REST ---
@api_router.get("/medicos")
def listar_medicos():
    return db_medicos.read()

@api_router.get("/consultas")
def listar_consultas():
    return db_consultas.read()

@api_router.post("/agendar")
async def criar_agendamento(agendamento: AgendamentoRequest):
    # [SO - LEITURA NÃO BLOQUEANTE]
    # O servidor lê o estado atual para verificar regras de negócio
    consultas_existentes = db_consultas.read()
    
    # Verifica conflito
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
    
    # [SO - PERSISTÊNCIA ATÔMICA]
    # Chama o método add() que contem o Mutex (Lock).
    # Aqui ocorre o bloqueio físico da thread de escrita.
    db_consultas.add(novo_agendamento)
    log_evento("INFO", f"Consulta agendada: Medico {agendamento.medico_id} às {agendamento.data_hora}")
    
    # [SO - CONSISTÊNCIA DE ESTADO]
    # Remove o lock da memória (Soft Lock) pois agora o dado está seguro no disco (Hard Lock).
    recurso_id_ws = f"{agendamento.medico_id}|{agendamento.data_hora}"
    manager.consume_lock(recurso_id_ws)
    
    # Broadcast
    await manager.broadcast({
        "tipo": "novo_agendamento",
        "dados": novo_agendamento
    })
    
    return {"msg": "Agendado com sucesso"}

@api_router.post("/cancelar")
async def cancelar_agendamento(req: CancelamentoRequest):
    consultas = db_consultas.read()
    
    # Filtra removendo a consulta alvo
    nova_lista = [c for c in consultas if not (c['medico_id'] == req.medico_id and c['data_hora'] == req.data_hora)]
    
    if len(nova_lista) < len(consultas):
        # Salva lista atualizada
        with db_consultas._lock:
            with open(db_consultas.filepath, 'w') as f:
                json.dump(nova_lista, f, indent=4)

        # [NOVO] Log
        log_evento("WARN", f"Consulta desocupada/cancelada: Medico {req.medico_id} às {req.data_hora}")

        await manager.broadcast({
            "tipo": "agendamento_cancelado",
            "medico_id": req.medico_id,
            "data_hora": req.data_hora
        })
        return {"msg": "Horário desocupado."}
    
    raise HTTPException(status_code=404, detail="Agendamento não encontrado.")