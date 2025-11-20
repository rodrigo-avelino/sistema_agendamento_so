from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List
import os

from src.storage import JsonStorage
from src.core.socket_manager import manager
from src.core.logger import log_evento, db_logs # [NOVO] Import do Logger

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

admin_router = APIRouter(prefix="/admin")

# [CORREÇÃO] Caminho dentro da subpasta 'consultas'
db_medicos = JsonStorage('consultas/medicos.json')

@admin_router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Renderiza o painel administrativo."""
    medicos = db_medicos.read()
    
    # [NOVO] Leitura real dos logs do sistema de arquivos
    logs_reais = db_logs.read()
    # Ordena por data (mais recente primeiro) e pega os últimos 50
    logs_reais = sorted(logs_reais, key=lambda x: x['timestamp'], reverse=True)[:50]

    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "medicos": medicos,
        "sistema_os": os.name,
        "logs": logs_reais # Envia os logs para o template HTML
    })

@admin_router.post("/medico/novo")
async def adicionar_medico(
    request: Request, 
    nome: str = Form(...), 
    especialidade: str = Form(...)
):
    """
    Adiciona um médico e avisa os clientes em tempo real.
    """
    novo_medico = {
        # [CORREÇÃO CRÍTICA] Removemos o 'id': 0. 
        # O JsonStorage.add vai gerar o ID automaticamente baseado no tamanho da lista.
        "nome": nome, 
        "especialidade": especialidade, 
        "ativo": True,
        "disponibilidade": {"dias": [], "horas": []} 
    }
    
    # 1. Persistência
    medico_salvo = db_medicos.add(novo_medico)
    
    # [NOVO] Log de Auditoria
    log_evento("ADMIN", f"Novo médico cadastrado: {nome} (ID: {medico_salvo['id']})")
    
    # 2. Broadcast
    print(f"[ADMIN] Novo médico adicionado: {medico_salvo['nome']}. Avisando clientes...")
    await manager.broadcast({
        "tipo": "novo_medico",
        "dados": medico_salvo
    })

    return RedirectResponse(url="/admin", status_code=303)

@admin_router.post("/medico/delete")
async def deletar_medico(medico_id: int = Form(...)):
    """
    Remove o médico e força saída dos clientes.
    """
    sucesso = db_medicos.delete(medico_id)
    
    if sucesso:
        # [NOVO] Log
        log_evento("ADMIN", f"Médico ID {medico_id} removido do sistema.")
        
        # Sincronização
        await manager.force_release_resource(str(medico_id))
        
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.post("/medico/horarios")
async def configurar_horarios(request: Request):
    """
    Atualiza a agenda com granularidade por dia.
    """
    form_data = await request.form()
    try:
        medico_id = int(form_data.get("medico_id"))
    except (TypeError, ValueError):
        return RedirectResponse(url="/admin", status_code=303)
    
    dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    nova_disponibilidade = {}
    
    # Coleta checkboxes
    for dia in dias_semana:
        horas_selecionadas = form_data.getlist(f"horas_{dia}")
        if horas_selecionadas:
            nova_disponibilidade[dia] = horas_selecionadas

    updates = {
        "disponibilidade": nova_disponibilidade
    }
    
    # Atualiza no disco
    db_medicos.update(medico_id, updates)
    
    # [NOVO] Log
    log_evento("ADMIN", f"Agenda atualizada para médico ID {medico_id}")
    
    # Sincroniza
    medicos = db_medicos.read()
    medico_atualizado = next((m for m in medicos if m["id"] == medico_id), None)
    
    if medico_atualizado:
        await manager.broadcast({
            "tipo": "atualizacao_medico",
            "dados": medico_atualizado
        })
    
    return RedirectResponse(url="/admin", status_code=303)