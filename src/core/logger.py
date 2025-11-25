import datetime
from src.storage import JsonStorage

# Variável global inicializada como None (Lazy Loading)
_db_logs_instance = None

def get_db_logs():
    """
    [PADRÃO SINGLETON/LAZY]
    Só inicializa o acesso ao arquivo quando for realmente necessário.
    Isso evita o erro de tentar criar arquivo antes das pastas existirem no boot.
    """
    global _db_logs_instance
    if _db_logs_instance is None:
        # Só agora tenta acessar o disco
        try:
            _db_logs_instance = JsonStorage('logs/system_logs.json')
        except Exception as e:
            print(f"[LOG CRITICAL] Falha ao iniciar sistema de logs: {e}")
            return None
    return _db_logs_instance

def log_evento(tipo: str, mensagem: str, usuario: str = "SYSTEM"):
    """
    Registra um evento no arquivo de log estruturado.
    """
    try:
        evento = {
            "timestamp": datetime.datetime.now().isoformat(),
            "tipo": tipo,
            "usuario": usuario,
            "mensagem": mensagem
        }
        
        # Imprime no terminal sempre (para debug visual)
        print(f"[{tipo}] {mensagem}")
        
        # Tenta gravar no disco
        storage = get_db_logs()
        if storage:
            storage.add(evento)
            
    except Exception as e:
        # Se o log falhar, não queremos derrubar o sistema inteiro
        print(f"!! ERRO AO GRAVAR LOG !!: {e}")