from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import os

from src.storage import JsonStorage
from src.core.socket_manager import manager
# [MUDANÇA] Importamos a função get_db_logs, não a variável direta
from src.core.logger import log_evento, get_db_logs 
from src.reports.generator import gerar_relatorio_pdf
from src.config.settings import RELATORIOS_DIR, TEMPLATES_DIR

templates = Jinja2Templates(directory=TEMPLATES_DIR)

admin_router = APIRouter(prefix="/admin")

db_medicos = JsonStorage('consultas/medicos.json')
db_consultas = JsonStorage('consultas/consultas.json')

@admin_router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    medicos = db_medicos.read()
    
    # [MUDANÇA] Usa a função para pegar o storage de forma segura
    logs_storage = get_db_logs()
    logs_reais = []
    if logs_storage:
        logs_reais = logs_storage.read()
        logs_reais = sorted(logs_reais, key=lambda x: x['timestamp'], reverse=True)[:50]

    # Listar relatórios
    arquivos_relatorios = []
    if os.path.exists(RELATORIOS_DIR):
        arquivos_relatorios = sorted(os.listdir(RELATORIOS_DIR), reverse=True)

    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "medicos": medicos,
        "sistema_os": os.name,
        "logs": logs_reais,
        "relatorios": arquivos_relatorios
    })

# ... (As outras rotas continuam iguais, pois usam log_evento que já está corrigido) ...

@admin_router.post("/relatorios/gerar")
async def gerar_relatorio(request: Request):
    form_data = await request.form()
    filtro_id = form_data.get("filtro_medico_id")
    
    consultas = db_consultas.read()
    medicos = db_medicos.read()
    
    consultas_filtradas = []
    
    if filtro_id and filtro_id != "todos":
        try:
            medico_id_int = int(filtro_id)
            consultas_filtradas = [c for c in consultas if c['medico_id'] == medico_id_int]
        except ValueError:
            consultas_filtradas = consultas
    else:
        consultas_filtradas = consultas

    arquivo = gerar_relatorio_pdf(consultas_filtradas, medicos)
    
    tipo = "Geral" if filtro_id == "todos" else f"Filtrado {filtro_id}"
    log_evento("ADMIN", f"Relatório gerado [{tipo}]: {arquivo}")
    
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.get("/relatorios/download/{filename}")
def download_relatorio(filename: str):
    file_path = os.path.join(RELATORIOS_DIR, filename)
    if os.path.exists(file_path):
        log_evento("ADMIN", f"Download: {filename}")
        return FileResponse(path=file_path, filename=filename, media_type='application/pdf')
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@admin_router.post("/medico/novo")
async def adicionar_medico(request: Request, nome: str = Form(...), especialidade: str = Form(...)):
    novo_medico = { "nome": nome, "especialidade": especialidade, "ativo": True, "disponibilidade": {"dias": [], "horas": []} }
    medico_salvo = db_medicos.add(novo_medico)
    log_evento("ADMIN", f"Novo médico: {nome}")
    await manager.broadcast({"tipo": "novo_medico", "dados": medico_salvo})
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.post("/medico/delete")
async def deletar_medico(medico_id: int = Form(...)):
    sucesso = db_medicos.delete(medico_id)
    if sucesso:
        log_evento("ADMIN", f"Médico {medico_id} deletado.")
        await manager.force_release_resource(str(medico_id))
    return RedirectResponse(url="/admin", status_code=303)

@admin_router.post("/medico/horarios")
async def configurar_horarios(request: Request):
    form_data = await request.form()
    try:
        medico_id = int(form_data.get("medico_id"))
    except: return RedirectResponse(url="/admin", status_code=303)
    
    dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    nova_disp = {}
    for d in dias:
        hs = form_data.getlist(f"horas_{d}")
        if hs: nova_disp[d] = hs

    db_medicos.update(medico_id, {"disponibilidade": nova_disp})
    log_evento("ADMIN", f"Agenda atualizada médico {medico_id}")
    
    medicos = db_medicos.read()
    medico_att = next((m for m in medicos if m["id"] == medico_id), None)
    if medico_att:
        await manager.broadcast({"tipo": "atualizacao_medico", "dados": medico_att})
    
    return RedirectResponse(url="/admin", status_code=303)