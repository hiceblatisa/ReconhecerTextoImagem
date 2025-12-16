import fitz 
import cv2
import numpy as np
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\isabela.sales\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
tessdata_dir_config = r'--tessdata-dir C:\Users\isabela.sales\AppData\Local\Programs\Tesseract-OCR\tessdata'

def preprocess_image(img):
    """Pré-processamento da imagem para melhorar OCR"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    return cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

def detect_signature(img, min_area=5000):
    """Detecta possíveis assinaturas na imagem"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    signatures = []
    for cnt in contours:
        if cv2.contourArea(cnt) > min_area:
            signatures.append(cv2.boundingRect(cnt))
    return signatures

def extract_text_from_pdf(pdf_path):
    """Extrai texto de PDF escaneado e detecta assinaturas"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    full_text = ""
    signature_pages = []

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:  # RGBA -> BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 1:  # grayscale -> BGR
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            processed_img = preprocess_image(img)

            data = pytesseract.image_to_data(processed_img, output_type='dict', config=tessdata_dir_config)
            words = [w for w in data.get('text', []) if w and w.strip()]
            page_text = " ".join(words)
            full_text += page_text + "\n"

            sigs = detect_signature(img)
            if sigs:
                signature_pages.append((page_num + 1, sigs))

    return full_text, signature_pages


