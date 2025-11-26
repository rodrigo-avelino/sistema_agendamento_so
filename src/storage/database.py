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
        
        # [SO - CONCORRÊNCIA] Primitiva de Sincronização (Mutex)
        # Este objeto Lock garante a Exclusão Mútua. Apenas uma thread pode
        # possuir este lock por vez.
        self._lock = threading.Lock()
        
        # Garante que o arquivo existe (Syscall de criação)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """
        [SO - SISTEMA DE ARQUIVOS]
        Verifica e cria o diretório e o arquivo se não existirem.
        Usa chamadas de sistema (os.makedirs, open).
        """
        directory = os.path.dirname(self.filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True) # Syscall: mkdir

        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f: # Syscall: open/write
                json.dump([], f)

    def read(self) -> List[Dict[str, Any]]:
        """
        Lê os dados do arquivo.
        [SO - PROBLEMA LEITORES/ESCRITORES]
        Protegemos até a leitura para evitar ler um arquivo que está sendo
        escrito pela metade (Dirty Read).
        """
        with self._lock: # Adquire o Mutex
            try:
                if not os.path.exists(self.filepath):
                    return []
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return [] 
            # O Lock é liberado automaticamente aqui

    def add(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adiciona um item ao arquivo JSON.
        [SO - REGIÃO CRÍTICA]
        Todo este bloco é atômico do ponto de vista das threads.
        """
        with self._lock: # [SO] Entra na Região Crítica (Acquire Lock)
            print(f"[SO - LOCK] Thread {threading.get_ident()} adquiriu o lock para {self.filepath}")
            
            # 1. Ler estado atual (I/O)
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    current_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                current_data = []
            
            # [SO - SIMULAÇÃO DE CARGA]
            # Simula um processamento pesado para provar que o Lock funciona.
            # Se outra thread tentar entrar aqui agora, ela ficará bloqueada (BLOCKED).
            time.sleep(2) 
            
            # 2. Modificar dados na Memória (Heap)
            if "id" not in item:
                item["id"] = len(current_data) + 1
            current_data.append(item)
            
            # 3. Escrever no disco (Persistência)
            # [SO - I/O WRITE] A escrita física ocorre aqui.
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=4, ensure_ascii=False)
                
            print(f"[SO - LOCK] Thread {threading.get_ident()} liberou o lock.")
            return item # [SO] Sai da Região Crítica (Release Lock)

    def update(self, item_id: int, updates: Dict[str, Any]) -> bool:
        """Atualiza um item existente de forma segura."""
        with self._lock: # [SO] Exclusão Mútua
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                return False
            
            found = False
            for i, item in enumerate(data):
                if item.get("id") == item_id:
                    data[i].update(updates)
                    found = True
                    break
            
            if found:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            
            return found

    def delete(self, item_id: int) -> bool:
        """Remove um item pelo ID de forma segura (Thread-Safe)."""
        with self._lock: # [SO] Exclusão Mútua
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return False

            original_len = len(data)
            data = [item for item in data if item.get("id") != item_id]
            
            if len(data) < original_len:
                time.sleep(0.5) 
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            
            return False