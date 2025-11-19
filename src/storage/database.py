import json
import os
import threading
import time
from typing import List, Dict, Any
# Importa os caminhos que definimos no passo anterior
from src.config.settings import CONSULTAS_DIR, DATA_DIR

class JsonStorage:
    def __init__(self, filename: str):
        """
        Inicializa o gerenciador de arquivo com um LOCK específico para este arquivo.
        Cada arquivo (medicos.json, consultas.json) terá seu próprio cadeado.
        """
        self.filepath = os.path.join(DATA_DIR, filename)
        # O objeto Lock é o mecanismo do SO para sincronização de threads
        self._lock = threading.Lock() 
        
        # Garante que o arquivo existe (cria vazio se não existir)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        # Lock não é estritamente necessário aqui se for chamado apenas no init, 
        # mas boas práticas de SO sugerem cautela.
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
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except json.JSONDecodeError:
                return [] # Retorna lista vazia se arquivo estiver corrompido/vazio

    def add(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adiciona um item ao arquivo JSON.
        Demonstração de SO: Região Crítica com atraso simulado.
        """
        # REGIÃO CRÍTICA: Apenas uma thread entra aqui por vez.
        with self._lock:
            print(f"[SO - LOCK] Thread {threading.get_ident()} adquiriu o lock para {self.filepath}")
            
            # 1. Ler estado atual
            with open(self.filepath, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            # 2. Processamento (Simulando carga pesada ou I/O lento)
            # Isso permite que você mostre na apresentação uma outra janela esperando!
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
            # Ler
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
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