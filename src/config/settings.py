import os
import sys
import platform

# --- 1. Detecção e Correção do Caminho Base ---
# [SO - GERÊNCIA DE PROCESSOS] 
# O sistema precisa saber se está rodando como um script interpretado (.py)
# ou como um processo binário compilado (Frozen/PyInstaller).
if getattr(sys, 'frozen', False):
    # [SO - FILE SYSTEM VIRTUAL] sys._MEIPASS é onde o PyInstaller descompacta os arquivos temporários
    BASE_DIR = sys._MEIPASS
    # Caminho físico onde o executável reside
    EXEC_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Modo Script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(current_dir))
    EXEC_DIR = BASE_DIR

# --- 2. Definição de Paths (Normalizados para o SO) ---
# [SO - ABSTRAÇÃO DE HARDWARE]
# platform.system() identifica o Kernel subjacente.
SYSTEM_OS = platform.system()

# [SO - PATH RESOLUTION]
# os.path.join usa o separador correto (\ para Windows, / para Linux)
# os.path.normpath resolve redundâncias no caminho
DATA_DIR = os.path.normpath(os.path.join(EXEC_DIR, 'data'))
LOGS_DIR = os.path.normpath(os.path.join(DATA_DIR, 'logs'))
CONSULTAS_DIR = os.path.normpath(os.path.join(DATA_DIR, 'consultas'))
RELATORIOS_DIR = os.path.normpath(os.path.join(DATA_DIR, 'relatorios'))

TEMPLATES_DIR = os.path.normpath(os.path.join(BASE_DIR, 'templates'))

# --- 3. Bootstrapper Automático ---
def init_filesystem():
    """
    [SO - BOOTSTRAPPING]
    Executa chamadas de sistema (syscalls) para preparar o ambiente.
    Equivalente a comandos 'mkdir' no shell.
    """
    if not os.path.exists(DATA_DIR):
        try:
            # Syscall: mkdir
            os.makedirs(DATA_DIR, exist_ok=True)
        except OSError:
            pass 

    dirs_to_create = [LOGS_DIR, CONSULTAS_DIR, RELATORIOS_DIR]
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"[BOOT] Diretório criado: {directory}")
            except OSError as e:
                print(f"[WARNING] Erro ao criar {directory}: {e}")

try:
    init_filesystem()
except Exception:
    pass