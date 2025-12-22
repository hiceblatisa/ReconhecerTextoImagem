"""Helpers leves de dataset para anotações de assinaturas.

Este módulo fornece utilitários mínimos para preparar a estrutura de
um dataset e criar um conjunto de exemplo. Não contém código de
treinamento nem referências a YOLO.
"""

from pathlib import Path
import shutil
import logging
import argparse
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def preparar_estrutura() -> None:
    """Cria diretórios e arquivo de configuração mínimo para o dataset.

    Garante que as pastas `dataset/images/{train,val}` e
    `dataset/labels/{train,val}` existam e escreve `dataset/assinaturas.yaml`.
    """

    pastas = [
        Path('dataset/images/train'),
        Path('dataset/images/val'),
        Path('dataset/labels/train'),
        Path('dataset/labels/val'),
        Path('models'),
    ]

    for p in pastas:
        p.mkdir(parents=True, exist_ok=True)
        logger.debug('Criado/confirmado: %s', p)

    config = {
        'path': str(Path('dataset').resolve()),
        'train': 'images/train',
        'val': 'images/val',
        'nc': 1,
        'names': ['assinatura'],
    }

    with open(Path('dataset') / 'assinaturas.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    logger.info('Estrutura de dataset criada em %s', Path('dataset').resolve())


def criar_dataset_exemplo(limit: int = 10) -> int:
    """Copia até `limit` imagens/PDFs (fora de `dataset/`) para `dataset/images/train`.

    Para PDFs, converte apenas a primeira página para JPEG (requer `fitz`/PyMuPDF).
    Gera labels fictícias para cada imagem copiada. Retorna o número de itens criados.
    """

    encontrados = []
    for ext in ('*.jpg', '*.png', '*.jpeg', '*.pdf'):
        for p in Path('.').rglob(ext):
            if 'dataset' in p.parts:
                continue
            encontrados.append(p)

    if not encontrados:
        logger.warning('Nenhuma imagem/PDF encontrada para criar exemplo')
        return 0

    selecionadas = encontrados[:limit]
    dest_dir = Path('dataset/images/train')
    dest_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for i, src in enumerate(selecionadas):
        try:
            if src.suffix.lower() == '.pdf':
                try:
                    import fitz
                except Exception:
                    logger.error('PyMuPDF (fitz) não disponível; ignorando %s', src)
                    continue
                doc = fitz.open(src)
                pix = doc.load_page(0).get_pixmap(dpi=150)
                dst = dest_dir / f'exemplo_{i}.jpg'
                pix.save(str(dst))
                doc.close()
            else:
                dst = dest_dir / f'exemplo_{i}{src.suffix}'
                shutil.copy2(src, dst)

            # criar label fictício
            label_path = Path('dataset/labels/train') / f'exemplo_{i}.txt'
            label_path.parent.mkdir(parents=True, exist_ok=True)
            with open(label_path, 'w', encoding='utf-8') as lf:
                lf.write('0 0.5 0.5 0.3 0.1\n')

            logger.info('Criado exemplo: %s', dst)
            count += 1
        except Exception as exc:
            logger.warning('Falha ao processar %s: %s', src, exc)

    logger.info('Criados %d exemplos em %s', count, dest_dir)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description='Helpers de dataset (sem YOLO)')
    parser.add_argument('--preparar', action='store_true', help='Prepara estrutura do dataset')
    parser.add_argument('--exemplo', action='store_true', help='Cria dataset de exemplo')
    parser.add_argument('--limit', type=int, default=10, help='Número máximo de exemplos a copiar')

    args = parser.parse_args()
    if args.preparar:
        preparar_estrutura()
    elif args.exemplo:
        preparar_estrutura()
        criar_dataset_exemplo(limit=args.limit)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
