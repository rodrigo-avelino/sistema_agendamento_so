import json
import os
import threading
import time
from typing import List, Dict, Any
from src.config.settings import DATA_DIR

class JsonStorage:
    def __init__(self, filename: str):
        """
        Inicializa o gerenciador de arquivo com um LOCK específico.
        """
        self.filepath = os.path.join(DATA_DIR, filename)
        # O objeto Lock é o mecanismo do SO para sincronização de threads
        self._lock = threading.Lock()
        
        # Garante que o arquivo existe
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """
        Verifica e cria o diretório e o arquivo se não existirem.
        """
        # [SO - DEFESA] Garante que a pasta pai existe antes de criar o arquivo
        directory = os.path.dirname(self.filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def read(self) -> List[Dict[str, Any]]:
        """
        Lê os dados do arquivo.
        Demonstração de SO: Leitura protegida (Leitores/Escritores).
        """
        # Adquire o cadeado. Se outra thread estiver escrevendo, esta linha TRAVA e espera.
        with self._lock:
            try:
                if not os.path.exists(self.filepath):
                    return []
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return [] 

    def add(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adiciona um item ao arquivo JSON.
        Demonstração de SO: Região Crítica com atraso simulado.
        """
        # REGIÃO CRÍTICA: Apenas uma thread entra aqui por vez.
        with self._lock:
            print(f"[SO - LOCK] Thread {threading.get_ident()} adquiriu o lock para {self.filepath}")
            
            # 1. Ler estado atual
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                current_data = []
            
            # 2. Processamento (Simulando carga pesada ou I/O lento)
            time.sleep(2) 
            
            # 3. Modificar dados
            # Gera ID simples baseado no tamanho da lista + 1
            if "id" not in item:
                item["id"] = len(current_data) + 1
            current_data.append(item)
            
            # 4. Escrever no disco (Persistência)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=4, ensure_ascii=False)
                
            print(f"[SO - LOCK] Thread {threading.get_ident()} liberou o lock.")
            return item

    def update(self, item_id: int, updates: Dict[str, Any]) -> bool:
        """Atualiza um item existente de forma segura."""
        with self._lock:
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                return False
            
            # Encontrar e atualizar
            found = False
            for i, item in enumerate(data):
                if item.get("id") == item_id:
                    data[i].update(updates)
                    found = True
                    break
            
            # Salvar apenas se mudou algo
            if found:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            
            return found
    def delete(self, item_id: int) -> bool:
        """Remove um item pelo ID de forma segura (Thread-Safe)."""
        with self._lock: # [SO] Exclusão Mútua para escrita
            try:
                # Lê o arquivo
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return False

            # Filtra a lista removendo o item com o ID especificado
            # (Cria uma nova lista sem o item)
            original_len = len(data)
            data = [item for item in data if item.get("id") != item_id]
            
            if len(data) < original_len:
                # Se o tamanho mudou, é porque removeu. Salva no disco.
                # [SO] Operação de I/O protegida
                time.sleep(0.5) # Pequeno delay para demonstrar o Lock se necessário
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            
            return False