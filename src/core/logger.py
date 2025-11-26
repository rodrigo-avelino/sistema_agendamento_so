import datetime
from src.storage import JsonStorage

# [SO - LAZY LOADING]
# Variável global inicializada como None. Só aloca recursos quando usada pela primeira vez.
_db_logs_instance = None

def get_db_logs():
    """
    Padrão Singleton para acesso ao arquivo de logs.
    Evita abrir múltiplos descritores de arquivo desnecessariamente.
    """
    global _db_logs_instance
    if _db_logs_instance is None:
        try:
            _db_logs_instance = JsonStorage('logs/system_logs.json')
        except Exception as e:
            print(f"[LOG CRITICAL] Falha ao iniciar logs: {e}")
            return None
    return _db_logs_instance

def log_evento(tipo: str, mensagem: str, usuario: str = "SYSTEM"):
    """
    [SO - LOGGING SEQUENCIAL]
    Realiza uma operação de escrita Append-Only (Adicionar ao final).
    Essencial para auditoria e recuperação de falhas (Journaling).
    """
    try:
        evento = {
            # Timestamp do SO
            "timestamp": datetime.datetime.now().isoformat(),
            "tipo": tipo,
            "usuario": usuario,
            "mensagem": mensagem
        }
        
        # Saída padrão (stdout) para debug imediato
        print(f"[{tipo}] {mensagem}")
        
        # Persistência em disco protegida por Lock (via JsonStorage)
        storage = get_db_logs()
        if storage:
            storage.add(evento)
            
    except Exception as e:
        print(f"!! ERRO AO GRAVAR LOG !!: {e}")