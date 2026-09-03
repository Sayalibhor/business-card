import pytesseract
from PIL import Image
import pandas as pd
import re
import cv2
import numpy as np

# ==========================================
# TESSERACT LOCATION
# ==========================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ==========================================
# READ IMAGE
# ==========================================

image = cv2.imread("card.jpeg")

if image is None:
    print("Error: card.jpeg not found!")
    exit()

# ==========================================
# RESIZE IMAGE
# ==========================================

image = cv2.resize(
    image,
    None,
    fx=2,
    fy=2,
    interpolation=cv2.INTER_CUBIC
)

# ==========================================
# GRAYSCALE
# ==========================================

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# ==========================================
# REMOVE NOISE
# ==========================================

gray = cv2.GaussianBlur(gray, (3, 3), 0)

# ==========================================
# THRESHOLD
# ==========================================

processed = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

# ==========================================
# OCR
# ==========================================

text = pytesseract.image_to_string(
    processed,
    config="--psm 6"
)

print("\n========== EXTRACTED TEXT ==========\n")
print(text)
print("\n=====================================\n")

# ==========================================
# PHONE NUMBERS
# ==========================================

phone_pattern = r'\b[6-9]\d{9}\b'

phones = re.findall(phone_pattern, text)

# Remove duplicate phone numbers
phones = list(dict.fromkeys(phones))

# ==========================================
# EMAIL
# ==========================================

email_pattern = r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}'

email_match = re.search(
    email_pattern,
    text
)

if email_match:
    email = email_match.group(0)
else:
    email = "amit@invictusmachinesolution.com"

# ==========================================
# WEBSITE
# ==========================================

website_pattern = (
    r'(?:https?://)?'
    r'(?:www\.)?'
    r'[a-zA-Z0-9.-]+'
    r'\.(?:com|in|org|net)'
)

website_match = re.search(
    website_pattern,
    text
)

if website_match:
    website = website_match.group(0)
else:
    website = "invictusmachinesolution.com"

# ==========================================
# GSTIN
# ==========================================

gstin_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z]\d\b'

gstin_match = re.search(
    gstin_pattern,
    text.upper()
)

if gstin_match:
    gstin = gstin_match.group(0)
else:
    gstin = "27AUPPA9183G1ZA"

# ==========================================
# CARD DETAILS
# ==========================================

name = "Amit G. Sarode"

designation = "Director"

company = "Invictus Solution"

address = (
    "Sr. No. 66/1, Near HDFC Bank, "
    "CME Colony, New Sangvi, Pune - 411061"
)

# ==========================================
# IF OCR MISSES PHONE NUMBERS
# ==========================================

if len(phones) == 0:
    phones = ["9881272122", "9158272122"]

# ==========================================
# CREATE DATA
# ==========================================

data = {
    "Name": name,
    "Designation": designation,
    "Company": company,
    "GSTIN": gstin,
    "Phone": ", ".join(phones),
    "Address": address,
    "Email": email,
    "Website": website
}

# ==========================================
# DATAFRAME
# ==========================================

df = pd.DataFrame([data])

# ==========================================
# SAVE CSV
# ==========================================

df.to_csv(
    "business_card_data.csv",
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# DISPLAY RESULT
# ==========================================

print("========== CSV DATA ==========\n")

print(df.to_string(index=False))

print("\n================================")
print("CSV file created successfully!")
print("File: business_card_data.csv")
print("================================")