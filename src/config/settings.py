import os
import sys
import platform

# --- 1. Detecção e Correção do Caminho Base ---
if getattr(sys, 'frozen', False):
    # [CORREÇÃO] MEIPASS para arquivos internos (templates)
    BASE_DIR = sys._MEIPASS
    # [CORREÇÃO] Caminho absoluto do executável para criar dados ao lado dele
    EXEC_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Modo Script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(current_dir))
    EXEC_DIR = BASE_DIR

# --- 2. Definição de Paths (Normalizados para o SO) ---
SYSTEM_OS = platform.system()

# Usa os.path.join e os.path.normpath para evitar barras misturadas (\ e /)
DATA_DIR = os.path.normpath(os.path.join(EXEC_DIR, 'data'))
LOGS_DIR = os.path.normpath(os.path.join(DATA_DIR, 'logs'))
CONSULTAS_DIR = os.path.normpath(os.path.join(DATA_DIR, 'consultas'))
RELATORIOS_DIR = os.path.normpath(os.path.join(DATA_DIR, 'relatorios'))

TEMPLATES_DIR = os.path.normpath(os.path.join(BASE_DIR, 'templates'))

# --- 3. Bootstrapper Automático ---
def init_filesystem():
    """Cria a estrutura de pastas necessária ao iniciar o sistema"""
    # Cria a pasta pai primeiro
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except OSError:
            pass # Ignora erro se já existir/concorrência

    dirs_to_create = [LOGS_DIR, CONSULTAS_DIR, RELATORIOS_DIR]
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"[BOOT] Diretório criado: {directory}")
            except OSError as e:
                # Apenas printa, não mata o programa aqui
                print(f"[WARNING] Erro ao criar {directory}: {e}")

# Tenta iniciar imediatamente, mas se falhar, o main.py tentará de novo
try:
    init_filesystem()
except Exception:
    pass