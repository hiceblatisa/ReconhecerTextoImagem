import os
import sys
import time
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReconhecerTextoImagem.validator import extract_text_from_pdf
from ReconhecerTextoImagem.ollama import OllamaFormatter, extrair_dados_com_ollama


def usar_sistema():
    """Processar um PDF e extrair dados (fluxo principal)."""
    print("\n" + "="*78)
    print(" EXTRAIR DADOS")
    print("="*78)

    tempo_inicio_total = time.time()

    pdf_path = r"C:\Users\isabela.sales\Documents\Desenvolvimento\projetos-python\ReconhecerTextoImagem\ReconhecerTextoImagem\imagens\93XSYKL1TNCM46554.pdf"
    if not os.path.exists(pdf_path):
        print(f"Erro: PDF não encontrado em {pdf_path}")
        return

    print(f"✓ Arquivo: {os.path.basename(pdf_path)}")

    try:
        texto_extraido, assinaturas = extract_text_from_pdf(pdf_path)
        print(f"✓ Texto extraído ({len(texto_extraido)} caracteres)")
        print(f"✓ Assinaturas detectadas: {len(assinaturas)}")
    except Exception as e:
        print(f" ERRO ao extrair texto: {e}")
        return

    formatter = OllamaFormatter()

    try:
        dados_ia = extrair_dados_com_ollama(texto_extraido, formatter.model)
    except SystemExit:
        print(" Extração com Ollama abortada.")
        return
    except Exception as e:
        print(f" Erro ao extrair dados com IA: {e}")
        return

    tempo_total = time.time() - tempo_inicio_total

    resultado_final = {
        "pdf_id": dados_ia.get("pdf_id", "") if isinstance(dados_ia, dict) else "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dados_extraidos": dados_ia if isinstance(dados_ia, dict) else {},
        "validacao": {
            "assinaturas_detectadas": len(assinaturas)
        },
        "processamento": {
            "duracao_ms": int(tempo_total * 1000)
        }
    }

    json_formatado = json.dumps(resultado_final, indent=2, ensure_ascii=False)
    print("\n" + "="*70)
    print("RESULTADO FINAL")
    print("="*70)
    print(json_formatado)

    output_dir = os.path.dirname(pdf_path)
    output_file = os.path.join(output_dir, "resultado.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado_final, f, indent=2, ensure_ascii=False)
        print(f" Resultado salvo em: {output_file}")
    except Exception as e:
        print(f" Erro ao salvar: {e}")

    print(f"\n✓ Processamento concluído em {tempo_total:.2f} segundos!")

def main():
    """Menu interativo"""
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*25 + "  LEITURA DE PDFs" + " "*26 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\nEscolha uma opção:")
    print("  1. Processar PDF")
    print("  2. Sair")
    escolha = input("\nOpção (1-2): ").strip()
    if escolha == "1":
        usar_sistema()
    elif escolha == "2":
        print("Saindo...")  
        return
    else:
        print("\nOpção inválida!")

if __name__ == "__main__":
    main()