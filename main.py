import uvicorn
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

# Imports internos
from src.config.settings import init_filesystem, SYSTEM_OS, BASE_DIR
from src.core.api import api_router
from src.core.admin import admin_router

# --- FUNÇÃO AUXILIAR PARA O PYINSTALLER ---
def get_resource_path(relative_path):
    """Retorna o caminho correto para o PyInstaller (_MEIPASS) ou dev local"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- CONFIGURAÇÃO DE LIFESPAN (Novo padrão do FastAPI) ---
# Substitui o on_event("startup") e "shutdown"
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print(f"\n--- [BOOT] INICIANDO SISTEMA NO {SYSTEM_OS.upper()} ---")
    # Bootstrapper (Cria pastas data/logs/consultas)
    init_filesystem()
    print("--- [BOOT] Sistema pronto.\n")
    
    yield # O sistema roda aqui
    
    # --- SHUTDOWN ---
    print("\n--- [SHUTDOWN] Encerrando...")

# --- INICIALIZAÇÃO DO APP ---
app = FastAPI(
    title="Sistema de Agendamento SO",
    version="1.0.0",
    lifespan=lifespan # Injeta a configuração de startup/shutdown
)

# 1. Resolver caminhos
templates_dir = get_resource_path("templates")
static_dir = get_resource_path("static")

# 2. Montar estáticos
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Montamos templates também como estático para garantir acesso se necessário
app.mount("/templates", StaticFiles(directory=templates_dir), name="templates")

# 3. Rotas
app.include_router(api_router)
app.include_router(admin_router)

@app.get("/client", response_class=HTMLResponse)
async def client_ui():
    client_path = os.path.join(templates_dir, "client.html")
    try:
        with open(client_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Erro crítico: Arquivo de template não encontrado no pacote.</h1>"

@app.get("/")
async def root():
    return RedirectResponse(url="/admin")

# --- EXECUÇÃO ---
if __name__ == "__main__":
    print("Acesse: http://localhost:8000/admin")
    
    # CORREÇÃO CRÍTICA AQUI:
    # 1. Passamos o objeto 'app' direto, não a string "main:app"
    # 2. reload=False OBRIGATÓRIO para executáveis
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=False, 
        log_level="info"
    )