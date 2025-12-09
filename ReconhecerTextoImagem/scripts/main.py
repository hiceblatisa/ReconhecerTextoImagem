
import json
import os
import sys
from pathlib import Path
import time


sys.path.insert(0, str(Path(__file__).parent.parent))

from ReconhecerTextoImagem.extractor import DataExtractor
# from ReconhecerTextoImagem.ollama_formatter import OllamaFormatter
from ReconhecerTextoImagem.validator import extract_text_from_pdf


def usar_sistema():
    """
    Processar um PDF e extrair dados
    """
    
    print("\n" + "="*70)
    print(" PROCESSAR PDF E EXTRAIR DADOS")
    print("="*70)
    
    tempo_inicio_total = time.time()
    tempo_inicio = time.time()

    print("\n[PASSO 1] Preparando o sistema...")
    
    extractor = DataExtractor()
    # formatter = OllamaFormatter()
    
    pdf_path = r"C:\Users\isabela.sales\Documents\Desenvolvimento\projetos-python\ReconhecerTextoImagem\ReconhecerTextoImagem\imagens\9BGEB48H0PG196930.pdf" #ALTERAR O CAMINHO DO PDF SE QUISER TESTAR OUTRO ARQUIVO
    
    if not os.path.exists(pdf_path):
        print(f"Erro: PDF não encontrado em {pdf_path}")
        return
    
    print(f"✓ Arquivo: {os.path.basename(pdf_path)}")
    tempo_fim = time.time()
    print(f"  Tempo: {tempo_fim - tempo_inicio:.2f} segundos")

    print("\n[PASSO 2] Extraindo texto do PDF com OCR...")
    tempo_inicio = time.time()
    
    try:
        texto_extraido, assinaturas = extract_text_from_pdf(pdf_path)
        print(f"✓ Texto extraído")
        print(f"✓ Assinaturas detectadas: {len(assinaturas)}")
    except Exception as e:
        print(f"✗ Erro ao extrair texto: {e}")
        return
    
    print("\n[PASSO 3] Extraindo campos...")
    
    dados_regex = extractor.extract_all(texto_extraido)
    
    campos_encontrados = sum(1 for v in dados_regex.values() if v)
    print(f"✓ {campos_encontrados}/7 campos encontrados")

    tempo_fim = time.time()
    print(f"  Tempo: {tempo_fim - tempo_inicio:.2f} segundos")
    
    print("\nDados extraídos com Regex:")
    for campo, valor in dados_regex.items():
        status = "✓" if valor else "✗"
        if valor:
            print(f"  {status} {campo:<20}: {valor}")
    
    # print("\n[PASSO 4] Verificando Ollama para refinamento...")
    
    # dados_final = extractor.extract_all(texto_extraido)
    
    # if formatter.check_ollama_connection():
    #     print("✓ Ollama detectado!")
        
    #     modelos = formatter.get_available_models()
    #     if modelos:
    #         formatter.set_model(modelos[0])
    #         print("✓ Refinando dados com LLM (pode levar alguns segundos)...")
            
    #         try:
    #             dados_final = formatter.format_with_ollama(texto_extraido)
    #             print("✓ Dados refinados com sucesso!")
    #         except Exception as e:
    #             print(f"! Erro ao chamar Ollama: {e}")
    #             print("  Usando apenas dados de Regex")
    #     else:
    #         print("✗ Nenhum modelo Ollama instalado")
    # else:
    #     print("✗ Ollama não disponível (não está rodando)")
    #     print("  Usando apenas dados de Regex")
    
    # print("\n[PASSO 5] Formatando resultado em JSON...")
    tempo_inicio = time.time()

    resultado_final = {
        "cpf_cnpj": dados_regex.get("cpf_cnpj", ""),
        "nome_devedor": dados_regex.get("nome_devedor", ""),
        "chassi": dados_regex.get("chassi", ""),
        "numero_contrato": dados_regex.get("numero_contrato", ""),
        "tipo_operacao": dados_regex.get("tipo_operacao", ""),
        "modelo_chassi": dados_regex.get("modelo_chassi", ""),
        "placa": dados_regex.get("placa", ""),
    }

    tempo_fim = time.time()
    print(f"  Tempo formatação: {tempo_fim - tempo_inicio:.2f} segundos")
    
    json_formatado = json.dumps(resultado_final, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("RESULTADO FINAL")
    print("="*70)
    print(json_formatado)
    

    print("\n[PASSO 4] Gerando JSON...")
    
    output_dir = os.path.dirname(pdf_path)
    output_file = os.path.join(output_dir, "resultado.json")
     
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado_final, f, indent=2, ensure_ascii=False)
        print(f"✓ Resultado salvo em: {output_file}")
    except Exception as e:
        print(f"✗ Erro ao salvar: {e}")

    tempo_fim_total = time.time()
    print(f"\nTempo Salvamento: {tempo_fim - tempo_inicio:.2f} segundos")

    tempo_fim_total = time.time()
    tempo_total = tempo_fim_total - tempo_inicio_total
   
    print("\n" + "="*70)
    print("Informações extraídas:")
    print("="*70)
    print(f"CPF/CNPJ: {dados_regex['cpf_cnpj']}")
    print(f"Nome: {dados_regex['nome_devedor']}")
    print(f"Chassi: {dados_regex['chassi']}")
    print(f"Contrato: {dados_regex['numero_contrato']}")
    print(f"Placa: {dados_regex['placa']}")
    print(f"Operação: {dados_regex['tipo_operacao']}")
    print("\n✓ Processamento concluído com sucesso!")
    print(f"\n✓ Processamento concluído em {tempo_total:.2f} segundos!")


def processar_lote(pasta):
    """
    Processar múltiplos PDFs de uma pasta
    """
    
    print("\n" + "="*70)
    print("PROCESSAR LOTE DE PDFs")
    print("="*70)
    tempo_inicio_total = time.time()
    
    if not os.path.exists(pasta):
        print(f"✗ Erro: Pasta não encontrada: {pasta}")
        return
    
    extractor = DataExtractor()
    # formatter = OllamaFormatter()
    
    resultados = []
    arquivos = list(Path(pasta).glob("*.pdf"))
    
    print(f"\nEncontrados {len(arquivos)} arquivo(s)")
    
    for idx, arquivo in enumerate(arquivos, 1):
        print(f"\n[{idx}/{len(arquivos)}] Processando: {arquivo.name}")
        tempo_arquivo_inicio = time.time()
        
        try:
            # OCR
            texto, _ = extract_text_from_pdf(str(arquivo))
            
            # Regex
            dados = extractor.extract_all(texto)
            
            # # Ollama (se disponível)
            # if formatter.check_ollama_connection():
            #     modelos = formatter.get_available_models()
            #     if modelos and idx == 1:  # Usar Ollama apenas para o primeiro
            #         formatter.set_model(modelos[0])
            #         dados = formatter.format_with_ollama(texto)
            
            resultados.append({
                "arquivo": arquivo.name,
                "status": "sucesso",
                "dados": dados
            })
            tempo_arquivo_fim = time.time()
            print(f"  ✓ Processado em {tempo_arquivo_fim - tempo_arquivo_inicio:.2f} segundos")
        
        except Exception as e:
            print(f"   Erro: {e}")
            resultados.append({
                "arquivo": arquivo.name,
                "status": "erro",
                "erro": str(e)
            })
    
    output_file = os.path.join(pasta, "resultados.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

        tempo_fim_total = time.time()
    tempo_total = tempo_fim_total - tempo_inicio_total
    
    print(f"\n✓ {len([r for r in resultados if r['status'] == 'sucesso'])}/{len(resultados)} sucesso")
    print(f"✓ Resultados salvos em: {output_file}")
    print(f"✓ Tempo total do lote: {tempo_total:.2f} segundos")
    print(f"✓ Média por arquivo: {tempo_total/len(arquivos):.2f} segundos")


def extrair_dados_texto(texto):
    """
    Extrair dados de um texto livre
    """
    
    print("\n" + "="*70)
    print("EXTRAIR DADOS DE TEXTO")
    print("="*70)

    tempo_inicio = time.time()
    
    extractor = DataExtractor()
    
    print("\nTexto de entrada:")
    print("-" * 50)
    print(texto)
    print("-" * 50)
    

    dados = extractor.extract_all(texto)
    
    print("\nDados extraídos:")
    for campo, valor in dados.items():
        if valor:
            print(f"  {campo}: {valor}")
    
  
    json_output = json.dumps(dados, indent=2, ensure_ascii=False)
    print("\nJSON:")
    print(json_output)

    tempo_fim = time.time()
    print(f"\n✓ Extração concluída em {tempo_fim - tempo_inicio:.2f} segundos")

# ============================================
# MENU PRINCIPAL
# ============================================

def main():
    """Menu interativo"""
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*25 + "  LEITURA DE PDFs" + " "*26 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\nEscolha uma opção:")
    print("  1. Processar PDF")
    print("  2. Processar lote de PDFs")
    print("  0. Sair")
    
    escolha = input("\nOpção (0-2): ").strip()
    
    if escolha == "1":
        usar_sistema()
    elif escolha == "2":
        pasta = r"C:\Users\isabela.sales\Documents\Desenvolvimento\projetos-python\ReconhecerTextoImagem\ReconhecerTextoImagem\imagens"
        processar_lote(pasta)
    elif escolha == "0":
        print("Saindo...")  
        return
    else:
        print("\nOpção inválida!")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
