"""
Módulo de reconhecimento e extração de texto de imagens
"""

from .validator import extract_text_from_pdf
from .extractor import DataExtractor
# from .ollama_formatter import OllamaFormatter

__version__ = "1.0.0"
__all__ = ["extract_text_from_pdf", "DataExtractor"]
