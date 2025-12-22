#!/usr/bin/env python3
"""Extrai crops candidatos a assinaturas para anotação manual.

Uso:
  python scripts/extract_signature_candidates.py --source ReconhecerTextoImagem/ReconhecerTextoImagem/imagens --out datasets/signatures/candidates

O script guarda crops em --out e gera um CSV com metadados para cada crop.
"""
import os
import sys
from pathlib import Path
import csv
import argparse

# garantir import do pacote local
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from ReconhecerTextoImagem.validator import detect_signature
except Exception:
    # fallback: implement simple contour detection here
    import cv2
    import numpy as np

    def detect_signature(img, min_area=5000):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                boxes.append(cv2.boundingRect(cnt))
        return boxes

import cv2
import numpy as np
try:
    import fitz
except Exception:
    fitz = None


def save_crop(img, bbox, out_dir: Path, base_name: str, idx: int, pad=8):
    x, y, w, h = bbox
    h_img, w_img = img.shape[:2]
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(w_img, x + w + pad)
    y2 = min(h_img, y + h + pad)
    crop = img[y1:y2, x1:x2]
    fname = f"{base_name}_crop_{idx}.jpg"
    path = out_dir / fname
    cv2.imwrite(str(path), crop)
    return path, (x1, y1, x2 - x1, y2 - y1)


def process_image_file(p: Path, out_dir: Path, csv_writer, prefix):
    img = cv2.imread(str(p))
    if img is None:
        return 0
    boxes = detect_signature(img)
    count = 0
    for i, b in enumerate(boxes):
        path, bbox2 = save_crop(img, b, out_dir, prefix, i)
        csv_writer.writerow([str(path), str(p), '', b[0], b[1], b[2], b[3]])
        count += 1
    return count


def process_pdf_file(p: Path, out_dir: Path, csv_writer, prefix):
    if fitz is None:
        print('PyMuPDF (fitz) não instalado; não é possível processar PDFs')
        return 0
    doc = fitz.open(str(p))
    total = 0
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        arr = np.frombuffer(pix.samples, dtype=np.uint8)
        img = arr.reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        boxes = detect_signature(img)
        for i, b in enumerate(boxes):
            path, bbox2 = save_crop(img, b, out_dir, f"{prefix}_p{page_num}", i)
            csv_writer.writerow([str(path), str(p), page_num, b[0], b[1], b[2], b[3]])
            total += 1
    return total


def main():
    parser = argparse.ArgumentParser(description='Extract signature candidate crops for manual labeling')
    parser.add_argument('--source', '-s', default='ReconhecerTextoImagem/ReconhecerTextoImagem/imagens', help='folder with images or PDFs')
    parser.add_argument('--out', '-o', default='datasets/signatures/candidates', help='output folder for crops and CSV')
    args = parser.parse_args()

    src = Path(args.source)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    csv_path = out / 'metadata.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['crop_path', 'source_file', 'page', 'x', 'y', 'w', 'h'])
        count = 0
        for p in src.iterdir():
            if p.is_dir():
                continue
            ext = p.suffix.lower()
            prefix = p.stem
            try:
                if ext == '.pdf':
                    n = process_pdf_file(p, out, writer, prefix)
                else:
                    n = process_image_file(p, out, writer, prefix)
                if n > 0:
                    print(f'Processed {p.name}: {n} candidates')
                count += n
            except Exception as e:
                print(f'Error processing {p}: {e}')

    print(f'Done. Total crops: {count}. Metadata: {csv_path}')
    print('Next steps: revise crops in the output folder, move accepted images to datasets/signatures/images/train (or val), and create corresponding labels in datasets/signatures/labels/{train,val} in YOLO format')


if __name__ == '__main__':
    main()
