from flask import Flask, render_template, request, jsonify
import cv2
import pytesseract
import pandas as pd
import re
import os

app = Flask(__name__)

# Tesseract
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

CSV_FILE = "scanned_cards.csv"


def extract_data(text):

    lines = [x.strip() for x in text.splitlines() if x.strip()]

    # Phone
    phones = re.findall(r'(?<!\d)[6-9]\d{9}(?!\d)', text)
    phone = ", ".join(dict.fromkeys(phones))

    # Email
    emails = re.findall(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )
    email = ", ".join(dict.fromkeys(emails))

    # GSTIN
    gst = re.findall(
        r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9]{2}\b',
        text.upper()
    )
    gstin = ", ".join(dict.fromkeys(gst))

    # Website
    websites = re.findall(
        r'(?:https?://)?(?:www\.)?[A-Za-z0-9-]+\.[A-Za-z]{2,}',
        text
    )
    websites = [x for x in websites if "@" not in x]
    website = ", ".join(dict.fromkeys(websites))

    # Designation
    designation = ""
    designation_words = [
        "director", "manager", "engineer", "developer",
        "designer", "founder", "ceo", "cfo", "cto",
        "owner", "executive", "consultant"
    ]

    for line in lines:
        if any(word in line.lower() for word in designation_words):
            designation = line
            break

    # Company
    company = ""
    company_words = [
        "pvt", "private", "limited", "ltd",
        "solution", "solutions", "technology",
        "technologies", "industries", "enterprise",
        "company", "corporation"
    ]

    for line in lines:
        if any(word in line.lower() for word in company_words):
            company = line
            break

    # Pincode
    pins = re.findall(r'\b\d{6}\b', text)
    pincode = pins[0] if pins else ""

    # City
    cities = [
        "Pune", "Mumbai", "Nashik", "Nagpur",
        "Thane", "Kolhapur", "Satara", "Sangli",
        "Solapur", "Aurangabad", "Pimpri", "Chinchwad"
    ]

    city = ""

    for c in cities:
        if c.lower() in text.lower():
            city = c
            break

    # Sr No
    sr = re.search(
        r'(?:Sr\.?\s*No\.?|S\.?\s*No\.?)\s*[:\-]?\s*(\d+(?:/\d+)?)',
        text,
        re.IGNORECASE
    )

    sr_no = sr.group(1) if sr else ""

    # Address
    address_words = [
        "road", "street", "near", "nagar", "colony",
        "pune", "mumbai", "maharashtra", "india",
        "shop", "floor", "building", "lane", "area"
    ]

    address_lines = []

    for line in lines:
        if any(word in line.lower() for word in address_words):
            if line != company and line != designation:
                if "@" not in line:
                    address_lines.append(line)

    address = ", ".join(address_lines)

    # Name
    name = ""

    for line in lines:

        if (
            len(line.split()) >= 2
            and len(line) < 50
            and not re.search(r'\d', line)
            and "@" not in line
            and line != company
            and line != designation
            and not any(x in line.lower() for x in address_words)
            and not any(x in line.lower() for x in company_words)
            and not any(x in line.lower() for x in designation_words)
        ):
            name = line
            break

    return {
        "Name": name,
        "Designation": designation,
        "Company": company,
        "GSTIN": gstin,
        "Phone": phone,
        "Email": email,
        "Website": website,
        "Address": address,
        "Sr No": sr_no,
        "City": city,
        "Pincode": pincode
    }


def save_csv(data):

    columns = [
        "Name", "Designation", "Company", "GSTIN",
        "Phone", "Email", "Website", "Address",
        "Sr No", "City", "Pincode"
    ]

    new_data = pd.DataFrame([data], columns=columns)

    if os.path.exists(CSV_FILE):
        old_data = pd.read_csv(CSV_FILE)
        final_data = pd.concat(
            [old_data, new_data],
            ignore_index=True
        )
    else:
        final_data = new_data

    final_data.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "Image not received"
        })

    file = request.files["image"]

    temp_file = "temp_card.jpg"
    file.save(temp_file)

    image = cv2.imread(temp_file)

    if image is None:
        return jsonify({
            "success": False,
            "message": "Image could not be read"
        })

    # OCR processing
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    text = pytesseract.image_to_string(
        processed,
        config="--psm 6"
    )

    data = extract_data(text)

    try:
        save_csv(data)
    except PermissionError:
        return jsonify({
            "success": False,
            "message": "Please close scanned_cards.csv and try again."
        })

    if os.path.exists(temp_file):
        os.remove(temp_file)

    return jsonify({
        "success": True,
        "data": data,
        "raw_text": text
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )