import datetime
from src.storage import JsonStorage

# [SO] Sistema de Arquivos: Define o caminho hierárquico correto
# Isso salvará em data/logs/system_logs.json
db_logs = JsonStorage('logs/system_logs.json')

def log_evento(tipo: str, mensagem: str, usuario: str = "SYSTEM"):
    """
    Registra um evento no arquivo de log estruturado (JSON).
    Demonstra operação de Append-Only em arquivo de log.
    """
    evento = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tipo": tipo,      # INFO, ERROR, WARN, ADMIN
        "usuario": usuario,
        "mensagem": mensagem
    }
    
    # Usa o Lock do storage para garantir escrita segura (Thread-Safe)
    try:
        db_logs.add(evento)
        # Imprime no terminal para debug imediato também
        print(f"[{tipo}] {mensagem}")
    except Exception as e:
        print(f"[LOG ERROR] Falha ao gravar log em disco: {e}")