import os
import sys
import platform

# --- 1. Detecção e Correção do Caminho Base ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # CORREÇÃO: Estávamos subindo um nível a mais. Agora está exato.
    # __file__ = .../src/config/settings.py
    # dirname  = .../src/config
    # dirname  = .../src
    # dirname  = .../sistema_agendamento (RAIZ CORRETA)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(current_dir))

# --- 2. Definição de Paths ---
SYSTEM_OS = platform.system()
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
CONSULTAS_DIR = os.path.join(DATA_DIR, 'consultas')
RELATORIOS_DIR = os.path.join(DATA_DIR, 'relatorios')

# --- 3. Bootstrapper Automático (Auto-Execução) ---
# Isso garante que as pastas sejam criadas ANTES de qualquer import de banco de dados
def init_filesystem():
    dirs_to_create = [DATA_DIR, LOGS_DIR, CONSULTAS_DIR, RELATORIOS_DIR]
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, mode=0o777, exist_ok=True)
                print(f"[BOOT] Diretório criado: {directory}")
            except OSError as e:
                print(f"[CRITICAL] Erro ao criar {directory}: {e}")

# Executa imediatamente ao importar este arquivo
init_filesystem()