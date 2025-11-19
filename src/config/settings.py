import os
import sys
import platform
import logging

# --- 1. Detecção de Ambiente (Conceito de SO) ---
# Verifica se está rodando como script (.py) ou executável congelado (.exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable) # Caminho do .exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Caminho do script
    # Ajuste para subir dois níveis (sair de src/config para a raiz)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))

# --- 2. Definição de Paths por SO [cite: 50] ---
SYSTEM_OS = platform.system()

# Caminhos absolutos para garantir que funcione em qualquer lugar
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
CONSULTAS_DIR = os.path.join(DATA_DIR, 'consultas')
RELATORIOS_DIR = os.path.join(DATA_DIR, 'relatorios')

# --- 3. Inicialização do Sistema de Arquivos (Bootstrapper) ---
def init_filesystem():
    """
    Cria a estrutura de diretórios necessária se não existir.
    Demonstra chamadas de sistema (mkdir) e manipulação de permissões.
    """
    dirs_to_create = [DATA_DIR, LOGS_DIR, CONSULTAS_DIR, RELATORIOS_DIR]
    
    created_any = False
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            try:
                # mode=0o777 garante permissão total (rwx) - Conceito de Permissões [cite: 51]
                os.makedirs(directory, mode=0o777, exist_ok=True) 
                print(f"[SYSTEM] Diretório criado: {directory}")
                created_any = True
            except OSError as e:
                print(f"[CRITICAL] Falha ao criar diretório {directory}: {e}")
                sys.exit(1)
    
    if created_any:
        print(f"[SYSTEM] Inicialização de diretórios concluída no {SYSTEM_OS}.")
    else:
        print("[SYSTEM] Estrutura de diretórios verificada. Tudo OK.")

# Configuração básica de Log
LOG_FILE = os.path.join(LOGS_DIR, 'system.log')