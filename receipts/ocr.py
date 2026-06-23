"""
OCR module using Tesseract to extract transaction data from receipt images.
All heavy imports (cv2, pytesseract) are deferred to function-call time so
the app starts even if these optional libraries are not installed.
"""
import re
from django.conf import settings


def preprocess_image(image_path: str):
    """Enhance image for better OCR accuracy. Returns processed numpy array."""
    try:
        import cv2
        import numpy as np
        img = cv2.imread(str(image_path))
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return thresh
    except ImportError:
        return None


def extract_text(image_path: str) -> str:
    """Run Tesseract OCR on the image and return raw text."""
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = getattr(settings, 'TESSERACT_CMD', '/usr/bin/tesseract')
        processed = preprocess_image(image_path)
        if processed is not None:
            text = pytesseract.image_to_string(processed, config='--psm 6')
        else:
            # Fallback: run OCR directly on the original image
            text = pytesseract.image_to_string(str(image_path), config='--psm 6')
        return text.strip()
    except Exception as e:
        return f"OCR Error: {e}"


def parse_receipt_data(text: str) -> dict:
    """
    Parse raw OCR text to extract:
    - total amount
    - merchant name
    - date
    - line items
    """
    data = {
        'merchant': '',
        'date': '',
        'total': None,
        'items': [],
        'raw': text,
    }

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Extract merchant name (usually first non-empty line)
    if lines:
        data['merchant'] = lines[0]

    # Extract total amount — look for patterns like "Total: 1,234.56" or "TOTAL 1234"
    total_patterns = [
        r'(?:total|grand total|amount|net amount)[:\s₹Rs.]*([0-9,]+\.?[0-9]*)',
        r'₹\s*([0-9,]+\.?[0-9]*)',
        r'Rs\.?\s*([0-9,]+\.?[0-9]*)',
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                data['total'] = float(amount_str)
                break
            except ValueError:
                pass

    # Extract date
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['date'] = match.group(1)
            break

    # Extract line items — "item name .... price"
    item_pattern = re.compile(r'^(.+?)\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*$')
    for line in lines[1:]:
        match = item_pattern.match(line)
        if match:
            name, price = match.groups()
            try:
                data['items'].append({'name': name.strip(), 'price': float(price.replace(',', ''))})
            except ValueError:
                pass

    return data
