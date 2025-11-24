from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from typing import List
import os

from src.storage import JsonStorage
from src.core.socket_manager import manager
from src.core.logger import log_evento, db_logs
from src.reports.generator import gerar_relatorio_pdf # <--- Import novo
from src.config.settings import RELATORIOS_DIR, TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)

admin_router = APIRouter(prefix="/admin")

db_medicos = JsonStorage('consultas/medicos.json')
db_consultas = JsonStorage('consultas/consultas.json') # Precisamos ler as consultas agora

@admin_router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Renderiza o painel administrativo."""
    medicos = db_medicos.read()
    
    # Logs
    logs_reais = db_logs.read()
    logs_reais = sorted(logs_reais, key=lambda x: x['timestamp'], reverse=True)[:50]

    # [NOVO] Listar arquivos de relatórios existentes (Conceito SO: Listar Diretório)
    arquivos_relatorios = []
    if os.path.exists(RELATORIOS_DIR):
        arquivos_relatorios = sorted(os.listdir(RELATORIOS_DIR), reverse=True)

    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "medicos": medicos,
        "sistema_os": os.name,
        "logs": logs_reais,
        "relatorios": arquivos_relatorios # Passamos a lista para o HTML
    })

# --- Rotas de Relatórios ---

@admin_router.post("/relatorios/gerar")
async def gerar_relatorio(request: Request):
    """
    Gera um novo PDF.
    Se vier um 'filtro_medico_id' no formulário, filtra as consultas.
    """
    form_data = await request.form()
    filtro_id = form_data.get("filtro_medico_id") # Pode ser "todos" ou um ID numérico
    
    # 1. Leitura dos dados (I/O Leitura)
    consultas = db_consultas.read()
    medicos = db_medicos.read()
    
    # 2. Filtragem (Processamento)
    consultas_filtradas = []
    nome_arquivo_sufixo = "geral"
    
    if filtro_id and filtro_id != "todos":
        try:
            medico_id_int = int(filtro_id)
            # Filtra apenas as consultas daquele médico
            consultas_filtradas = [c for c in consultas if c['medico_id'] == medico_id_int]
            
            # Tenta achar o nome do médico para o log e nome do arquivo
            medico_obj = next((m for m in medicos if m['id'] == medico_id_int), None)
            if medico_obj:
                nome_arquivo_sufixo = medico_obj['nome'].replace(" ", "_")
        except ValueError:
            consultas_filtradas = consultas # Fallback se der erro
    else:
        consultas_filtradas = consultas # Relatório completo

    # 3. Geração do PDF (I/O Escrita)
    # Passamos apenas as consultas filtradas para o gerador
    arquivo = gerar_relatorio_pdf(consultas_filtradas, medicos)
    
    # Renomeia o arquivo para facilitar identificação (Opcional, mas elegante)
    # O gerador cria com timestamp. Se quiser, podemos manter o nome original ou fazer um log detalhado.
    
    tipo_relatorio = "Geral" if filtro_id == "todos" else f"Filtrado (Médico ID {filtro_id})"
    log_evento("ADMIN", f"Relatório gerado [{tipo_relatorio}]: {arquivo}")
    
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.get("/relatorios/download/{filename}")
def download_relatorio(filename: str):
    """Serve o arquivo para download (Conceito SO: File Streaming)."""
    file_path = os.path.join(RELATORIOS_DIR, filename)
    
    if os.path.exists(file_path):
        log_evento("ADMIN", f"Download de relatório: {filename}")
        return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
    
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

# --- Rotas de Médicos (Mantidas iguais, apenas resumidas aqui) ---

@admin_router.post("/medico/novo")
async def adicionar_medico(request: Request, nome: str = Form(...), especialidade: str = Form(...)):
    novo_medico = {
        "nome": nome, 
        "especialidade": especialidade, 
        "ativo": True,
        "disponibilidade": {"dias": [], "horas": []} 
    }
    medico_salvo = db_medicos.add(novo_medico)
    log_evento("ADMIN", f"Novo médico cadastrado: {nome} (ID: {medico_salvo['id']})")
    await manager.broadcast({"tipo": "novo_medico", "dados": medico_salvo})
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.post("/medico/delete")
async def deletar_medico(medico_id: int = Form(...)):
    sucesso = db_medicos.delete(medico_id)
    if sucesso:
        log_evento("ADMIN", f"Médico ID {medico_id} removido.")
        await manager.force_release_resource(str(medico_id))
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.post("/medico/horarios")
async def configurar_horarios(request: Request):
    form_data = await request.form()
    try:
        medico_id = int(form_data.get("medico_id"))
    except: return RedirectResponse(url="/admin", status_code=303)
    
    dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    nova_disponibilidade = {}
    for dia in dias_semana:
        horas = form_data.getlist(f"horas_{dia}")
        if horas: nova_disponibilidade[dia] = horas

    db_medicos.update(medico_id, {"disponibilidade": nova_disponibilidade})
    log_evento("ADMIN", f"Agenda atualizada médico {medico_id}")
    
    medicos = db_medicos.read()
    medico_atualizado = next((m for m in medicos if m["id"] == medico_id), None)
    if medico_atualizado:
        await manager.broadcast({"tipo": "atualizacao_medico", "dados": medico_atualizado})
    
    return RedirectResponse(url="/admin", status_code=303)