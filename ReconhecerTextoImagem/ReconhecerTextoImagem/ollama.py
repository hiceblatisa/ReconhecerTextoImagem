
import requests
import json
import re
import sys
import time
from typing import Dict, List

class OllamaFormatter:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "phi3:mini"):
        self.ollama_url = ollama_url
        self.model = model

    def set_model(self, model_name: str):
        if isinstance(model_name, str) and model_name:
            self.model = model_name
        else:
            print(f"Atenção: Tentativa de definir modelo inválido: {model_name}")
            print("   Usando modelo padrão: phi3:mini")
            self.model = "phi3:mini"

    def extract_with_ollama(self, text: str) -> Dict[str, str]:
        prompt = (
            "Do texto abaixo, retorne os campos chassi, marca, ano, placa e cor, se tiver; se não, pode deixar nulo. Retorne apenas JSON válido.\n"
            + text
        )
        print(" Enviando requisição para o Ollama...")
        start_request = time.time()
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 800,
                        "num_ctx": 4096
                    }
                },
                timeout=300
            )
            request_time = time.time() - start_request
            if response.status_code != 200:
                print(f"\n ERRO CRÍTICO: Ollama retornou código {response.status_code}")
                print(f"   Tempo da requisição: {request_time:.2f}s")
                sys.exit(1)
            response_data = response.json()
            response_text = response_data.get("response", "")
            print("\n====== RESPOSTA DO OLLAMA ======")
            print(response_text)
            print("====== FIM DA RESPOSTA ======\n")
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    extracted_data = json.loads(json_str)
                else:
                    print("\n ERRO: Ollama não retornou JSON válido!")
                    print(f"   Tempo da requisição: {request_time:.2f}s")
                    print(f"   Resposta recebida: {response_text[:200]}...")
                    sys.exit(1)
            except json.JSONDecodeError as e:
                print("\n ERRO: Falha ao decodificar JSON do Ollama!")
                print(f"  Tempo da requisição: {request_time:.2f}s")
                print(f" Erro: {e}")
                print(f" Resposta completa:")
                print(response_text)
                sys.exit(1)
            print(f" Tempo total da requisição: {request_time:.2f}s")
            return extracted_data
        except Exception as e:
            print(f"\n ERRO: Falha inesperada: {e}")
            sys.exit(1)

    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponíveis no Ollama (ou lista vazia em falha)."""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "models" in data:
                    return [m.get("name", "") for m in data["models"]]
        except Exception:
            pass
        return []

def extrair_dados_com_ollama(texto_pdf: str, modelo: str = "phi3:mini") -> Dict[str, str]:
    formatter = OllamaFormatter(model=modelo)
    return formatter.extract_with_ollama(texto_pdf)


def extrair_dados_com_ollama(texto_pdf: str, modelo: str = "phi3:mini") -> Dict[str, str]:
    """
    Função principal para extrair dados com Ollama (aborta se falhar)
    """
    print("\n" + "="*78)
    print("EXTRAÇÃO COM OLLAMA")
    print("="*78)
    
    formatter = OllamaFormatter()
    
   
    formatter.set_model(modelo)
    
    modelos_disponiveis = formatter.get_available_models()
    if modelos_disponiveis:
        print(f" Verificando modelos...")
 
    start_time = time.time()
    
    try:
        resultado = formatter.extract_with_ollama(texto_pdf)
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Extração concluída em {elapsed_time:.2f} segundos")
        
        return resultado
        
    except SystemExit:
        print("\n" + "="*71)
        print("PROCESSAMENTO ABORTADO - OLLAMA COM FALHA")
        print("="*71)
        sys.exit(1)
    except Exception as e:
        print(f"\n ERRO INESPERADO: {e}")
        sys.exit(1)

