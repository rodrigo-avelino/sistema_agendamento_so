import uvicorn
import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Imports dos nossos módulos
from src.config.settings import init_filesystem, SYSTEM_OS, BASE_DIR
from src.core.api import api_router
from src.core.admin import admin_router

# --- 1. Configuração da Aplicação ---
app = FastAPI(
    title="Sistema de Agendamento SO",
    description="Backend demonstrativo de conceitos de Sistemas Operacionais",
    version="1.0.0"
)

# --- 2. Montagem de Arquivos Estáticos e Rotas ---
# Necessário para o Jinja2 achar os templates quando rodar
app.mount("/static", StaticFiles(directory="src/templates"), name="static")

# Inclui as rotas que criamos (API React e Admin)
app.include_router(api_router)
app.include_router(admin_router)

# --- 3. Eventos de Ciclo de Vida (Startup/Shutdown) ---
@app.on_event("startup")
async def startup_event():
    """
    Executado quando o processo do servidor inicia.
    Conceito SO: Inicialização de ambiente.
    """
    print(f"--- [BOOT] INICIANDO SISTEMA NO {SYSTEM_OS.upper()} ---")
    
    # Garante que as pastas data/logs/consultas existam
    init_filesystem()
    
    print(f"--- [BOOT] Diretório base: {BASE_DIR}")
    print("--- [BOOT] Sistema de arquivos pronto e verificado.")

@app.on_event("shutdown")
async def shutdown_event():
    print("--- [SHUTDOWN] Liberando recursos e encerrando threads...")

# --- 4. Ponto de Entrada (Execução) ---
if __name__ == "__main__":
    # Verifica se é executado diretamente (python main.py)
    # Configuração do servidor web (Uvicorn)
    # host="0.0.0.0" permite acesso externo na rede local (necessário para testar em 2 PCs)
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True, # Recarrega se alterar código (apenas em dev)
        log_level="info"
    )