import uvicorn
import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse

# Imports dos nossos módulos internos
from src.config.settings import init_filesystem, SYSTEM_OS, BASE_DIR
from src.core.api import api_router
from src.core.admin import admin_router

# --- 1. Configuração da Aplicação ---
app = FastAPI(
    title="Sistema de Agendamento SO",
    description="Backend demonstrativo de conceitos de Sistemas Operacionais (Threads, Filesystem, IPC)",
    version="1.0.0"
)

# --- 2. Montagem de Arquivos Estáticos ---
# Serve a pasta 'templates' na URL /static (necessário para o CSS/JS se houver no futuro)
# e permite que o Jinja2 encontre os arquivos HTML
app.mount("/static", StaticFiles(directory="templates"), name="static")

# --- 3. Inclusão de Rotas (Modularização) ---
app.include_router(api_router)    # Rotas da API (React + WebSocket)
app.include_router(admin_router)  # Rotas do Painel Administrativo

# --- 4. Rota para a Interface de Teste do Cliente (HTML Puro) ---
@app.get("/client", response_class=HTMLResponse)
async def client_ui():
    """
    Serve a interface de cliente de simulação (Client A / Client B).
    Lê o arquivo HTML do disco e retorna para o navegador.
    Demonstração de leitura de arquivo estático simples.
    """
    # Garante o caminho correto independente de onde o script é rodado
    client_path = os.path.join("templates", "client.html")
    
    try:
        with open(client_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Erro: Arquivo templates/client.html não encontrado.</h1>"

# --- 5. Rota Raiz (Redireciona para o Admin) ---
@app.get("/")
async def root():
    return RedirectResponse(url="/admin")

# --- 6. Eventos de Ciclo de Vida (Startup/Shutdown) ---
@app.on_event("startup")
async def startup_event():
    """
    Executado quando o processo do servidor inicia.
    Conceito SO: Inicialização de ambiente e verificação de integridade.
    """
    print(f"\n--- [BOOT] INICIANDO SISTEMA NO {SYSTEM_OS.upper()} ---")
    print(f"--- [BOOT] PID do Processo: {os.getpid()}")
    
    # Garante que as pastas data/logs/consultas existam antes de aceitar conexões
    init_filesystem()
    
    print(f"--- [BOOT] Diretório base: {BASE_DIR}")
    print("--- [BOOT] Sistema de arquivos verificado. Servidor pronto.\n")

@app.on_event("shutdown")
async def shutdown_event():
    print("\n--- [SHUTDOWN] Encerrando conexões e liberando descritores de arquivo...")

# --- 7. Ponto de Entrada (Execução) ---
if __name__ == "__main__":
    # Verifica se é executado diretamente (python main.py)
    # Configuração do servidor web (Uvicorn)
    print("Acesse o Admin em: http://localhost:8000/admin")
    print("Acesse o Cliente em: http://localhost:8000/client")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", # Permite acesso externo na rede local
        port=8000, 
        reload=True,    # Reinicia se alterar código (apenas dev)
        log_level="info"
    )