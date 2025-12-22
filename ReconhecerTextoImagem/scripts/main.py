import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ReconhecerTextoImagem.validator import extract_text_from_pdf, extract_fields_from_text
from ReconhecerTextoImagem.ollama import OllamaFormatter, extrair_dados_com_ollama


def processar_pdf(pdf_path, model="phi3:mini"):
    """Processa um PDF de forma otimizada"""
    print("\n" + "="*60)
    print(" EXTRAIR DADOS")
    print("="*60)
    
    if not os.path.exists(pdf_path):
        print(f"Erro: PDF não encontrado: {pdf_path}")
        return
    
    print(f"Arquivo: {os.path.basename(pdf_path)}")
    start_time = time.time()
    
    # 1. Extrair texto do PDF
    try:
        texto_extraido, assinaturas = extract_text_from_pdf(pdf_path)
        total_assinaturas = sum(page['count'] for page in assinaturas)
        print(f"✓ Texto extraído: {len(texto_extraido)} caracteres")
        print(f"✓ Assinaturas detectadas: {total_assinaturas}")
    except Exception as e:
        print(f"Erro na extração de texto: {e}")
        return
    # 2. Extrair dados com IA (Ollama)
    dados_ia = {}
    try:
        texto_limitado = texto_extraido[:40000]  
        
        formatter = OllamaFormatter()
        dados_ia = extrair_dados_com_ollama(texto_limitado, model)
        
        if isinstance(dados_ia, str):
            try:
                dados_ia = json.loads(dados_ia)
                print(f"✓ Dados extraídos via Ollama: {dados_ia}")
            except:
                dados_ia = {}
                
    except Exception as e:
        print(f"Aviso: Ollama não disponível, usando heurística: {e}")
        dados_ia = {}
    
    campos_heuristica = extract_fields_from_text(texto_extraido, pdf_path, assinaturas)
    
    dados_finais = campos_heuristica.copy()
    if isinstance(dados_ia, dict):
        for chave, valor in dados_ia.items():
            if valor and (not dados_finais.get(chave) or dados_finais[chave] in [None, "", []]):
                dados_finais[chave] = valor
    
    resultado = {
        "pdf": os.path.basename(pdf_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dados": dados_finais,
        "processamento": {
            "duracao_segundos": round(time.time() - start_time, 2),
            "assinaturas_detectadas": total_assinaturas,
             "metodo": "Ollama + Heurística" if dados_ia else "Apenas Heurística"
        }
    }
    
    print("\n" + "="*60)
    print("RESULTADO")
    print("="*60)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    campos_prioritarios = [
        'tipo_documento', 'contrato', 'grupo', 'cota',
        'nome_devedor', 'devedor', 'cpf_cnpj',
        'saldo_devedor', 'chassi', 'placa', 'uf',
        'marca', 'modelo', 'ano', 'cor',
        'credora', 'assinatura_presente'
    ]
    
    print("\n INFORMAÇÕES DO CONTRATO:")
    for campo in campos_prioritarios:
        if campo in dados_finais and dados_finais[campo] not in [None, "", []]:
            valor = dados_finais[campo]
            if campo == 'assinatura_presente':
                valor = "SIM" if valor else " NÃO"
            print(f"   {campo.replace('_', ' ').title()}: {valor}")
    
    outros_campos = [c for c in dados_finais.keys() if c not in campos_prioritarios]
    if outros_campos:
        print(f"\n Outros campos encontrados ({len(outros_campos)}):")
        for campo in sorted(outros_campos)[:10]:  
            if dados_finais[campo] not in [None, "", []]:
                print(f"   • {campo}")
    
    output_dir = os.path.dirname(pdf_path)
    nome_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"resultado_{nome_base}.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"\n Resultado salvo em: {output_file}")
    except Exception as e:
        print(f" Erro ao salvar: {e}")
    
    print(f"\n Processamento concluído em {resultado['processamento']['duracao_segundos']} segundos")
    print("="*70)
    
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
        for pdf in pdfs[:3]: 
            processar_pdf(str(pdf), args.model)
    else:
        print("\n" + "="*60)
        print(" EXTRATOR DE DADOS DE PDF")
        print("="*60)
        
        caminho = input("\nCaminho do PDF ou pasta: ").strip()
        if not caminho:
            return
        
        if os.path.isdir(caminho):
            pdfs = list(Path(caminho).glob("*.pdf"))
            for i, pdf in enumerate(pdfs[:3]):  
                print(f"\n[{i+1}/{min(3, len(pdfs))}] Processando: {pdf.name}")
                processar_pdf(str(pdf), "phi3:mini")
        else:
            processar_pdf(caminho, "phi3:mini")


if __name__ == "__main__":
    main()