import re
import json
import time
from typing import Dict, Optional


class DataExtractor:
    """Extrai dados estruturados de texto usando regex"""

    def __init__(self):
        self.patterns = {
            # CPF: XXX.XXX.XXX-XX
            "cpf": r"\d{3}\.\d{3}\.\d{3}-\d{2}",
            # CNPJ: XX.XXX.XXX/XXXX-XX
            "cnpj": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
            # Ambos CPF e CNPJ (sem formatação também)
            "cpf_cnpj_unformatted": r"(?:\d{11}|\d{14})",
            # Chassi (17 caracteres alfanuméricos)
            "chassi": r"(?i)[A-HJ-NPR-Z0-9]{17}",
            # Placa (formato antigo: AAA-NNNN ou novo: NNNNANNNN)
            "placa_antiga": r"[A-Z]{3}-?\d{4}",
            "placa_nova": r"[A-Z]{3}-?[0-9]{1}[A-Z]{1}[0-9]{2}",
            # Número de contrato (variações possíveis)
            "numero_contrato": r"(?:(?:Contrato|Nº|Nº.)\s*)?(?:#)?\s*(\d{6,20})",
        }
  # Palavras-chave para identificar nomes em documentos
        self.nome_keywords = [
            "devedor", "devedora", "mutuario", "mutuaria", 
            "consorciado", "consorciada", "tomador", "tomadora",
            "nome", "razao social", "razao", "empresa", 
            "cliente", "contratante", "participante"
        ]
        
        # Abreviações comuns em nomes de empresas
        self.company_suffixes = [
            "SA", "LTDA", "ME", "EPP", "EIRELI", "SC", "S/S", 
            "S.A", "LTD", "INC", "COM", "S/C", "COOP"
        ]

    def preprocess_text(self, text: str) -> str:
        """
        Pós-processamento do texto (corrigir erros comuns do OCR)
        
        Args:
            text: Texto extraído do PDF
            
        Returns:
            Texto processado e normalizado
        """
        if not text:
            return ""
            
        # Converte para minúsculas para padronização
        text = text.lower().strip()
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text)
        
        # Limpa quebras de linha
        text = re.sub(r'[\n\r]+', '\n', text)
        
        # Corrige 'O' ou 'o' como '0' em números (erro comum de OCR)
        # Exemplo: "o123" ou "O456" se torna "0123" ou "0456"
        text = re.sub(r'[oO]\s*([1-9])', r'0\1', text)
        
        # Corrige 'l' (letra ele) confundido com '1' ou 'I'
        text = re.sub(r'\bl([0-9])', r'1\1', text)  # l seguido de número
        
        # Corrige '|' (pipe) ou '/' confundidos com '1'
        text = re.sub(r'[|/]\s*([0-9])', r'1\1', text)
        
        # Corrige 'S' confundido com '5' em contexto de números
        text = re.sub(r'(\d)\s*s\s*(\d)', r'\1 5 \2', text)
        text = re.sub(r'(\d)\s*s\s*(\d)', r'\1 5 \2', text)

        # Normaliza pontuação
        text = re.sub(r'[.,;:]{2,}', '.', text)
        
        # Remove caracteres especiais não desejados
        text = re.sub(r'[_*\\\[\]\(\)\{\}\"]', ' ', text)
        
        # Normaliza espaços novamente após as correções
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_cpf_cnpj(self, text: str) -> Optional[str]:
        """Extrai CPF ou CNPJ do texto"""
        # Tenta CNPJ primeiro (mais específico)
        match = re.search(self.patterns["cnpj"], text, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # Depois tenta CPF
        match = re.search(self.patterns["cpf"], text, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # Tenta versão sem formatação (11 ou 14 dígitos)
        match = re.search(self.patterns["cpf_cnpj_unformatted"], text)
        if match:
            value = match.group(0)
            if len(value) == 11:
                return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
            elif len(value) == 14:
                return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"
        
        return ""

    def extract_nome_devedor(self, text: str) -> str:
        """Extrai nome do devedor"""
        # Procura após palavras-chave comuns
        patterns_nome = [
            # Padrão de tabela: |Devedor(a) NOME|...
            r'Devedor\(a\)\s+([A-Z][A-Z\s\.&]+(?:SA|LTDA|MEI?|EPP|EIRELI|S\/A|S\.A)?)\b',
            # Padrão após dois pontos
            r'Devedor[:\s]+([A-Z][A-Z\s\.&]+(?:SA|LTDA|MEI?|EPP|EIRELI)?)',
            # Procura por texto em maiúsculas após "Devedor"
            r'(?i)devedor[^\n]*?([A-Z][A-Z\s\.&]{3,})',
        ]
        
        for pattern in patterns_nome:
            match = re.search(pattern, text)
            if match:
                nome = match.group(1).strip()
                # Remove números e caracteres especiais desnecessários
                nome = re.sub(r'[\d\|\[\]\{\}\(\)]', '', nome)
                nome = re.sub(r'\s+', ' ', nome).strip()
                if len(nome) > 3 and not re.match(r'^\d+$', nome):
                    return nome
        
        return ""

    def extract_chassi(self, text: str) -> str:
        """Extrai número do chassi"""
        # Procura após palavra-chave "chassi"
        patterns_chassi = [
        r'(?i)chassi[:\s]*([A-HJ-NPR-Z0-9]{17})',
        r'(?i)vin[:\s]*([A-HJ-NPR-Z0-9]{17})',
        r'\b([A-HJ-NPR-Z0-9]{17})\b', 
        ]
        for pattern in patterns_chassi:
            match = re.search(pattern, text)
            if match:
                return match.group(1).upper()
    
        return ""

    def extract_placa(self, text: str) -> str:
        """Extrai placa veicular"""
        patterns_placa = [
            r"(?:placa|placas?|pla)[\s:]*([A-Z]{3}-?[0-9]{4}|[A-Z]{3}[0-9][A-Z][0-9]{2})",
            r"([A-Z]{3}-[0-9]{1}[A-Z][0-9]{2})",  # Placa Mercosul
            r"([A-Z]{3}\d{4})",  # Sem hífen
        ]
        
        for pattern in patterns_placa:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                placa = match.group(1).upper().replace("-", "")
                if re.match(r"[A-Z]{3}[0-9A-Z]{4}", placa):
                    return f"{placa[:3]}-{placa[3:]}"
        
        return ""

    def extract_numero_contrato(self, text: str) -> str:
        """Extrai número do contrato"""
        patterns_contrato = [
            r"(?:contrato|contrato\s?numero|numero\s?contrato|nº\.?\s?contrato|numero do contrato)[\s:]*#?(\d{6,20})",
            r"(?:nº|nº\.)\s*(\d{6,20})",
            r"contrato[\s:]*(\d{6,20})",
            r"numero[\s:]*(\d{6,20})",
             r'\|\s*\d{3}\s*\|\s*(\d{6,8})\s*\|[^|]*33[.,]',
            r'[Cc]ontrato[:\s]+(\d{6,8})\b',
            r'[Cc]ota.*?(\d{6,8})\b',
        ]
        
        for pattern in patterns_contrato:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""

    def extract_tipo_operacao(self, text: str) -> str:
        """Detecta tipo de operação"""
        text_lower = text.lower()
        
        # Verifica cada tipo (ordem importa - mais específicas primeiro)
        if re.search(r"alienacao\s+fiduciaria|alienacao fiduciaria|aliencao fiduciaria", text_lower):
            return "alienacao fiduciaria"
        
        if re.search(r"aditamento|aditado|aditivamento|aditivado|termo aditivo", text_lower):
            return "aditamento"
        
        if re.search(r"compra(?:\s+de)?\s+veiculo|compra veiculo|aquisicao\s+de\s+veiculo|aquisicao veiculo", text_lower):
            return "compra de veiculo"
        
        if re.search(r"registro(?:\s+de)?\s+contrato|registr\w*\s+contrato", text_lower):
            return "registro de contrato"
        
        return ""

    def extract_modelo_chassi(self, text: str) -> str:
        """Extrai modelo do chassi/veículo"""
        patterns = [
            r"(?:modelo do chassi|modelo\s?:)[\s]*([A-Z0-9\s\-\.]{2,50})",
            r"(?:modelo)[\s:]*([A-Z][A-Z0-9\s\-]{1,48})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                modelo = match.group(1).strip()
                modelo = re.sub(r"\s+", " ", modelo).rstrip(".,;:")
                if len(modelo) > 1:
                    return modelo
        
        return ""

    def extract_ano_modelo(self, text: str) -> str:
        """Extrai ano e modelo do veículo"""
        # Procura por padrão ano/modelo
        patterns = [
            r"(?:ano|ano\s?de|ano\s?/\s?modelo)[\s:]*(\d{4})\s*/?[\s\-]?([A-Z0-9\s\-]{1,50})",
            r"(\d{4})\s*/?[\s\-]?\s*([A-Z][A-Z0-9\s\-]{1,48})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ano = match.group(1)
                modelo = match.group(2).strip() if len(match.groups()) > 1 else ""
                return f"{ano} {modelo}".strip()
        
        return ""

    # def extract_ano(self, text: str) -> str:
    #     """Extrai apenas o ano"""
    #     match = re.search(self.patterns["ano_numero"], text)
    #     if match:
    #         return match.group(0)
    #     return ""

    def extract_all(self, text: str) -> Dict[str, str]:
        text_clean = self.preprocess_text(text)
        """Extrai todos os dados de uma vez"""
        return {
            "cpf_cnpj": self.extract_cpf_cnpj(text_clean),
            "nome_devedor": self.extract_nome_devedor(text_clean),
            "chassi": self.extract_chassi(text_clean),
            "numero_contrato": self.extract_numero_contrato(text_clean),
            "tipo_operacao": self.extract_tipo_operacao(text_clean),
            "modelo_chassi": self.extract_modelo_chassi(text_clean),
            "placa": self.extract_placa(text_clean),
            # "ano": self.extract_ano(text),
        }


if __name__ == "__main__":
    # Teste
    extractor = DataExtractor()
    
    texto_teste = """
    CONTRATO DE ALIENAÇÃO FIDUCIÁRIA
    
    Devedor: João da Silva Santos
    CPF: 123.456.789-00
    
    Contrato nº 202312345678
    
    Chassi: 9BWSU29J005678901
    Placa: ABC-1234
    Modelo: Gol 1.6
    Ano: 2023
    
    Tipo de Operação: Alienação Fiduciária
    """
    
    dados = extractor.extract_all(texto_teste)
    print(json.dumps(dados, indent=2, ensure_ascii=False))
