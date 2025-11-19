from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

from src.storage import JsonStorage

# Configuração do Jinja2 (Templates HTML)
# Caminho absoluto para funcionar no executável
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

admin_router = APIRouter(prefix="/admin")
db_medicos = JsonStorage('medicos.json')
db_logs = JsonStorage('system_logs.json') # Futuro log [cite: 36]

@admin_router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Renderiza o painel administrativo."""
    medicos = db_medicos.read()
    # Passamos 'request' e 'medicos' para o HTML
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "medicos": medicos,
        "sistema_os": os.name # Passa info do SO para mostrar na tela
    })

@admin_router.post("/medico/novo")
def adicionar_medico(
    request: Request,
    nome: str = Form(...), 
    especialidade: str = Form(...)
):
    """
    Adiciona um médico. 
    IMPORTANTE: Ao clicar em salvar aqui, o JsonStorage.add será chamado.
    Como colocamos um 'time.sleep(2)' lá no database.py, o sistema vai 'pensar'.
    Se alguém tentar agendar no React nesse momento, vai ter que esperar o Lock liberar.
    """
    novo_medico = {
        "nome": nome,
        "especialidade": especialidade,
        "ativo": True
    }
    db_medicos.add(novo_medico)
    
    # Redireciona de volta para o dashboard e atualiza a lista
    return admin_dashboard(request)