import os
import sys
import platform

# --- 1. Detecção e Correção do Caminho Base ---
if getattr(sys, 'frozen', False):
    # [CORREÇÃO CRÍTICA]
    # Se for executável (PyInstaller), os recursos (templates) estão
    # descompactados na pasta temporária sys._MEIPASS, e não ao lado do executável.
    BASE_DIR = sys._MEIPASS
else:
    # Se estiver rodando como script normal
    # __file__ = .../src/config/settings.py -> sobe 3 níveis para chegar na raiz
    current_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(current_dir))

# --- 2. Definição de Paths (Caminhos) ---
SYSTEM_OS = platform.system()

# A pasta 'data' deve ser criada AO LADO do executável (Externo), para persistir
# Se for frozen, usamos sys.executable para pegar a pasta onde o usuário clicou
if getattr(sys, 'frozen', False):
    EXEC_DIR = os.path.dirname(sys.executable)
else:
    EXEC_DIR = BASE_DIR

# Pastas de DADOS (Ficam fora para não sumir quando fecha o exe)
DATA_DIR = os.path.join(EXEC_DIR, 'data')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
CONSULTAS_DIR = os.path.join(DATA_DIR, 'consultas')
RELATORIOS_DIR = os.path.join(DATA_DIR, 'relatorios')

# Pasta de RECURSOS (Fica dentro do executável/MEIPASS)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# --- 3. Bootstrapper Automático (Auto-Execução) ---
def init_filesystem():
    """Cria a estrutura de pastas necessária ao iniciar o sistema"""
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