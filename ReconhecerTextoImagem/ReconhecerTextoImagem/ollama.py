import requests
import json
import time
import re
from typing import Dict, Optional


class OllamaFormatter:
    def __init__(self, url="http://localhost:11434", model="phi3:mini"):
        self.url = url
        self.model = model
        # Aumentamos o timeout global para evitar quedas em textos longos
        self.timeout = 300

    def extract_json(self, texto: str) -> Optional[Dict]:
        """Extrai dados estruturados do texto"""

        # Melhoramos o prompt para ser mais imperativo e definimos o esquema esperado
        prompt = f"""Extraia do texto:
- nome_devedor
- cpf_cnpj  
- contrato
- grupo
- cota
- saldo_devedor
- chassi
- placa
- uf
- credora
Retorne em JSON.
Texto do contrato:
---
{texto[:25000]}
---
Retorne apenas o JSON:"""

        try:
            # Enviamos a requisição com o timeout estendido
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Força o Ollama a tentar responder em formato JSON
                    "options": {
                        "temperature": 0.0,  # Zero torna a resposta determinística (mais precisa)
                        "num_predict": 1000,
                        "num_ctx": 32000  # Aumenta a janela de contexto para ler o texto todo
                    }
                },
                timeout=self.timeout  # Alterado de 45 para 300
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')

                # Tentar extrair JSON da resposta
                json_match = self._extract_json_from_text(response_text)
                if json_match:
                    return json_match

                return {"erro": "A IA respondeu mas o formato não era JSON", "raw": response_text[:200]}

            print(f"Erro Ollama (Status {response.status_code}): {response.text}")
            return None

        except requests.exceptions.Timeout:
            print(f"Erro: O Ollama demorou mais de {self.timeout}s para processar.")
            return {"erro": "Timeout na conexão com Ollama"}
        except Exception as e:
            print(f"Erro ao chamar Ollama: {e}")
            return {"erro": str(e)}

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Tenta extrair JSON da resposta do modelo usando Regex"""
        try:
            # Tenta carregar direto primeiro
            return json.loads(text)
        except json.JSONDecodeError:
            # Se falhar, tenta achar o bloco {} com Regex
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, text)
            if match:
                try:
                    return json.loads(match.group())
                except:
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