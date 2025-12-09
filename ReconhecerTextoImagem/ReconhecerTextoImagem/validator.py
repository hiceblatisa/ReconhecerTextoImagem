import fitz  # PyMuPDF
import cv2
import numpy as np
import pytesseract
import os

# Configuração do Tesseract (ajuste conforme sua instalação)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\isabela.sales\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
tessdata_dir_config = r'--tessdata-dir C:\Users\isabela.sales\AppData\Local\Programs\Tesseract-OCR\tessdata'

def preprocess_image(img):
    """Pré-processamento da imagem para melhorar OCR"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return processed

def detect_signature(img, min_area=5000):
    """Detecta possíveis assinaturas na imagem"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    signatures = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:  # ajuste mínimo para considerar como assinatura
            x, y, w, h = cv2.boundingRect(cnt)
            signatures.append((x, y, w, h))
    return signatures

def extract_text_from_pdf(pdf_path):
    """Extrai texto de PDF escaneado e detecta assinaturas"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    doc = fitz.open(pdf_path)
    full_text = ""
    signature_pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:  # RGBA -> RGB
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

        # Pré-processamento para OCR
        processed_img = preprocess_image(img)

        # OCR
        data = pytesseract.image_to_data(processed_img, output_type='dict', config=tessdata_dir_config)
        page_text = ""
        for i, word in enumerate(data['text']):
            if word.strip() != "":
                try:
                    conf = int(data['conf'][i])
                    if conf < 0:
                        conf = 50
                except:
                    conf = 50
                page_text += word + " "
        full_text += page_text + "\n"

        # Detecção de assinatura
        sigs = detect_signature(img)
        if sigs:
            signature_pages.append((page_num + 1, sigs))

    return full_text, signature_pages

if __name__ == "__main__":
    pdf_path = r"C:\Users\isabela.sales\Documents\Desenvolvimento\projetos-python\ReconhecerTextoImagem\ReconhecerTextoImagem\imagens\8AJJC3GS6M0157024.pdf"
    texto_extraido, assinaturas = extract_text_from_pdf(pdf_path)

    print("====== TEXTO EXTRAÍDO ======")
    print(texto_extraido)
    print("====== PÁGINAS COM ASSINATURA ======")
    if assinaturas:
        for page, boxes in assinaturas:
            print(f"Página {page}, Assinaturas detectadas: {len(boxes)}")
    else:
        print("Nenhuma assinatura detectada")
