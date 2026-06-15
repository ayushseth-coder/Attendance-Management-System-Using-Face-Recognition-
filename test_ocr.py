import traceback
import pytesseract
from PIL import Image

try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    print("Tesseract Version:", pytesseract.get_tesseract_version())
except Exception as e:
    print("Tesseract Error:")
    traceback.print_exc()
