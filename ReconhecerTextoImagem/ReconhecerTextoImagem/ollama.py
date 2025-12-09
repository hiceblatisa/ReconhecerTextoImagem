# import requests
# import json
# from typing import Dict, Optional
# from .extractor import DataExtractor


# class OllamaFormatter:
#     """Formata dados extraídos usando Ollama LLM local"""

#     def __init__(self, ollama_url: str = "http://localhost:11434"):
#         self.ollama_url = ollama_url
#         self.model = "qwen2.5:7b"
#         self.extractor = DataExtractor()
        
#         # Caminho do executável Ollama no Windows
#         self.ollama_exe = r"C:\Users\isabela.sales\AppData\Local\Programs\Ollama\ollama.exe"

#     def set_model(self, model_name: str):
#         """Define o modelo Ollama a ser usado"""
#         self.model = model_name

#     def check_ollama_connection(self) -> bool:
#         """Verifica se Ollama está disponível"""
#         try:
#             response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
#             return response.status_code == 200
#         except Exception as e:
#             print(f"Erro ao conectar com Ollama: {e}")
#             return False

#     def get_available_models(self) -> list:
#         """Retorna modelos disponíveis no Ollama"""
#         try:
#             response = requests.get(f"{self.ollama_url}/api/tags")
#             data = response.json()
#             if "models" in data:
#                 return [model["name"] for model in data["models"]]
#             return []
#         except Exception as e:
#             print(f"Erro ao buscar modelos: {e}")
#             return []

#     def create_extraction_prompt(self, text: str, extracted_data: Dict[str, str]) -> str:
#         """Cria um prompt para a LLM extrair e formatar os dados"""
#         prompt = f"""Você é um modelo especialista em extração de dados.
# Receberá texto bruto extraído via OCR de um PDF.
# Analise o seguinte texto extraído de um documento e organize os dados em JSON.

# TEXTO EXTRAÍDO:
# {text}


# Por favor, complemente e corrija os dados extraídos se necessário. Retorne APENAS um JSON válido com a seguinte estrutura, preenchendo com "" (vazio) se não encontrar o dado:

# {{
#     "cpf_cnpj": "",
#     "nome_devedor": "",
#     "chassi": "",
#     "numero_contrato": "",
#     "tipo_operacao": "",
#     "modelo_chassi": "",
#     "placa": "",
#     "ano": ""
# }}

# Regras importantes:
# - CPF/CNPJ: Formato XXX.XXX.XXX-XX para CPF ou XX.XXX.XXX/XXXX-XX para CNPJ (no JSON, não coloque formatação)
# - Nome: Completamente em maiúsculas com espaços, validar se o nome está proximo do campo nome/devedor
# - Chassi: 17 caracteres alfanuméricos (sem formatação)
# - Placa: Formato ABC-1234 ou ABC1D23 (Mercosul)
# - Tipo de operação: aditamento, compra de veículo, alienação fiduciária ou registro de contrato
# - Número do contrato: Apenas números
# - Ano: 4 dígitos (19XX ou 20XX)

# Retorne APENAS o JSON, sem explicações adicionais."""
        
#         return prompt

#     def format_with_ollama(self, text: str) -> Dict[str, str]:
#         """Formata dados usando Ollama"""
#         extracted_data = self.extractor.extract_all(text)
        
#         prompt = self.create_extraction_prompt(text, extracted_data)
        
#         try:
            
#             response = requests.post(
#                 f"{self.ollama_url}/api/generate",
#                 json={
#                     "model": self.model,
#                     "prompt": prompt,
#                     "stream": False,
#                 },
#                 timeout=240  # Aumentado de 60 para 120 segundos
#             )
            
#             if response.status_code != 200:
#                 print(f"Erro na resposta do Ollama: {response.status_code}")
#                 return extracted_data
            
#             response_data = response.json()
#             response_text = response_data.get("response", "")
            
          
#             try:
              
#                 import re
#                 json_match = re.search(r'\{[\s\S]*\}', response_text)
#                 if json_match:
#                     json_str = json_match.group(0)
#                     formatted_data = json.loads(json_str)
#                     return formatted_data
#                 else:
#                     print("Nenhum JSON encontrado na resposta do Ollama")
#                     return extracted_data
#             except json.JSONDecodeError as e:
#                 print(f"Erro ao fazer parse do JSON da resposta: {e}")
#                 return extracted_data
        
#         except requests.exceptions.Timeout:
#             print("Timeout ao chamar Ollama")
#             return extracted_data
#         except Exception as e:
#             print(f"Erro ao chamar Ollama: {e}")
#             return extracted_data

#     def format_json(self, text: str) -> str:
#         """Formata o resultado final em JSON string"""
#         result = self.format_with_ollama(text)
        
#         final_result = {
#             "cpf_cnpj": result.get("cpf_cnpj", ""),
#             "nome_devedor": result.get("nome_devedor", ""),
#             "chassi": result.get("chassi", ""),
#             "numero_contrato": result.get("numero_contrato", ""),
#             "tipo_operacao": result.get("tipo_operacao", ""),
#             "modelo_chassi": result.get("modelo_chassi", ""),
#             "placa": result.get("placa", ""),
#             "ano_modelo": result.get("ano_modelo", ""),
#             "ano": result.get("ano", ""),
#         }
        
#         return json.dumps(final_result, indent=2, ensure_ascii=False)


# if __name__ == "__main__":
#     formatter = OllamaFormatter()
    

#     if not formatter.check_ollama_connection():
#         print("Ollama nao esta disponivel ")
#         print("Modelos disponíveis ainda serão extraídos por regex")
#     else:
#         print("OK - Conectado ao Ollama")
#         modelos = formatter.get_available_models()
#         print(f"Modelos disponíveis: {modelos}")
    
#     texto_teste = """
#     CONTRATO DE ALIENACAO FIDUCIARIA
    
#     Devedor: Joao da Silva Santos
#     CPF: 123.456.789-00
    
#     Contrato numero 202312345678
    
#     Chassi: 9BWSU29J005678901
#     Placa: ABC-1234
#     Modelo: Gol 1.6
#     Ano: 2023
#     """
    
#     print("\n" + "="*50)
#     print("RESULTADO:")
#     print("="*50)
#     resultado = formatter.format_json(texto_teste)
#     print(resultado)
