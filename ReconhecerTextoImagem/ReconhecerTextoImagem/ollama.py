import requests
import json
import time
from typing import Dict, Optional


class OllamaFormatter:
    def __init__(self, url="http://localhost:11434", model="phi3:mini"):
        self.url = url
        self.model = model
        self.timeout = 300
    
    def extract_json(self, texto: str) -> Optional[Dict]:
        """Extrai dados estruturados do texto"""
        prompt = f"""Analise o texto abaixo e extraia os seguintes campos de um contrato de alienação fiduciária: nome_devedor (nome completo do devedor fiduciário), cpf_cnpj (CPF ou CNPJ do devedor), contrato (número do contrato), grupo, cota, valor do saldo devedor, chassi (número do chassi  placa, uf, credora (instituição financeira), retorne APENAS JSON válido com esses campos. Se algum campo não estiver presente, retorne-o como null.
        Texto:
        {texto[:30000]}
        """
        
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1,
                    "num_predict": 1000
                    }     
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Tentar extrair JSON da resposta
                json_match = self._extract_json_from_text(response_text)
                if json_match:
                    return json_match
                
                return {"raw_response": response_text[:500]}  # Fallback
            
            print(f"Erro Ollama: {response.status_code}")
            return None
            
        except requests.exceptions.Timeout:
            print("Timeout na conexão com Ollama")
            return None
        except Exception as e:
            print(f"Erro ao chamar Ollama: {e}")
            return None
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Tenta extrair JSON da resposta do modelo"""
        import re
        
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        return None


def extrair_dados_com_ollama(texto: str, modelo: str = "phi3:mini") -> Dict:
    """Interface principal para extração com Ollama"""
    formatter = OllamaFormatter(model=modelo)
    
    try:
        resultado = formatter.extract_json(texto)
        return resultado or {}
    except Exception as e:
        print(f"Erro na extração Ollama: {e}")
        return {}