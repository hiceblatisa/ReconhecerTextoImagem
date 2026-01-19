import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Ajuste de path para importar módulos locais
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReconhecerTextoImagem.validator import extract_text_from_pdf
from ReconhecerTextoImagem.ollama import OllamaFormatter, extrair_dados_com_ollama


def processar_pdf(pdf_path, model="phi3:mini"):
    """Processa um PDF de forma otimizada"""
    print("\n" + "=" * 60)
    print(" INICIANDO PROCESSAMENTO")
    print("=" * 60)

    if not os.path.exists(pdf_path):
        print(f"Erro: PDF não encontrado: {pdf_path}")
        return

    print(f"Arquivo: {os.path.basename(pdf_path)}")
    start_time = time.time()

    # 1. Extrair texto do PDF (OCR)
    try:
        texto_extraido, assinaturas = extract_text_from_pdf(pdf_path)
        total_assinaturas = sum(len(sigs) for _, sigs in assinaturas)

        print("\n" + "-" * 20 + " TEXTO EXTRAÍDO (OCR) " + "-" * 20)
        # Exibe o texto extraído para conferência
        print(texto_extraido)
        print("-" * 60)

        print(f"✓ Tamanho do texto: {len(texto_extraido)} caracteres")
        print(f"✓ Assinaturas detectadas: {total_assinaturas}")
    except Exception as e:
        print(f"Erro na extração de texto: {e}")
        return

    # 2. Extrair dados com IA (Ollama)
    print(f"\nEnviando para IA ({model})... aguarde.")
    dados_ia = {}
    try:
        # Limitamos o texto para não estourar o contexto da maioria dos modelos locais
        texto_limitado = texto_extraido[:40000]
        dados_ia = extrair_dados_com_ollama(texto_limitado, model)

        if isinstance(dados_ia, str):
            try:
                dados_ia = json.loads(dados_ia)
            except:
                dados_ia = {"erro": "Falha ao converter resposta da IA para JSON", "conteudo_bruto": dados_ia}
        print(f"✓ Processamento IA concluído")
    except Exception as e:
        print(f"Erro no processamento Ollama: {e}")
        dados_ia = {"erro": str(e)}

    # 3. Montagem do Objeto de Resultado
    duracao = round(time.time() - start_time, 2)
    resultado = {
        "arquivo": os.path.basename(pdf_path),
        "processamento": {
            "duracao_segundos": duracao,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "modelo": model
        },
        "dados": dados_ia
    }

    # 4. Exibição dos Campos Solicitados no Terminal
    print("\n" + "=" * 60)
    print(" CAMPOS SOLICITADOS")
    print("=" * 60)

    campos_prioritarios = [
        'tipo_documento', 'contrato', 'grupo', 'cota',
        'nome_devedor', 'devedor', 'cpf_cnpj',
        'saldo_devedor', 'chassi', 'placa', 'uf',
        'marca', 'modelo', 'ano', 'cor',
        'credora', 'assinatura_presente'
    ]

    # Se a IA retornou um erro, avisa aqui
    if "erro" in dados_ia and len(dados_ia) == 1:
        print(f"AVISO: A IA não conseguiu extrair os campos. Erro: {dados_ia['erro']}")
    else:
        for campo in campos_prioritarios:
            # Busca o valor dentro de dados_ia
            valor = dados_ia.get(campo)

            # Formatação visual
            if valor not in [None, "", []]:
                if campo == 'assinatura_presente':
                    valor = "SIM" if (valor is True or str(valor).upper() == "SIM") else "NÃO"

                nome_campo = campo.replace('_', ' ').title()
                print(f" {nome_campo:.<25}: {valor}")
            else:
                print(f" {campo.replace('_', ' ').title():.<25}: [Não encontrado]")

    # 5. Salvar em arquivo JSON
    output_dir = os.path.dirname(pdf_path)
    nome_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"resultado_{nome_base}.json")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"\n[💾] JSON completo salvo em: {output_file}")
    except Exception as e:
        print(f" Erro ao salvar arquivo: {e}")

    print(f"\nTempo total: {duracao}s")
    print("=" * 60)

    return resultado


def main():
    parser = argparse.ArgumentParser(description="Extrair dados de PDFs")
    parser.add_argument('--pdf', help='Caminho para arquivo PDF')
    parser.add_argument('--dir', help='Diretório com PDFs')
    parser.add_argument('--model', default='phi3:mini', help='Modelo Ollama a usar')
    args = parser.parse_args()

    if args.pdf:
        processar_pdf(args.pdf, args.model)
    elif args.dir:
        pdfs = list(Path(args.dir).glob("*.pdf"))
        for pdf in pdfs:
            processar_pdf(str(pdf), args.model)
    else:
        print("\n" + "=" * 60)
        print(" EXTRATOR DE DADOS DE PDF")
        print("=" * 60)

        caminho = input("\nCaminho do PDF ou pasta: ").strip().replace('"', '')
        if not caminho:
            return

        if os.path.isdir(caminho):
            pdfs = list(Path(caminho).glob("*.pdf"))
            for i, pdf in enumerate(pdfs):
                print(f"\n[{i + 1}/{len(pdfs)}] Processando: {pdf.name}")
                processar_pdf(str(pdf), args.model)
        else:
            processar_pdf(caminho, args.model)


if __name__ == "__main__":
    main()