from flask import Flask, render_template, request, jsonify
import cv2
import pytesseract
import pandas as pd
import re
import os

app = Flask(__name__)


# =====================================================
# TESSERACT PATH
# =====================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =====================================================
# FILE PATH
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NEW CSV FILE
CSV_FILE = os.path.join(
    BASE_DIR,
    "business_card_data.csv"
)

# NEW EXCEL FILE
EXCEL_FILE = os.path.join(
    BASE_DIR,
    "business_card_data.xlsx"
)

# TEMP IMAGE
TEMP_FILE = os.path.join(
    BASE_DIR,
    "temp_card.jpg"
)


# =====================================================
# EXTRACT DATA
# =====================================================

def extract_data(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # =================================================
    # PHONE
    # =================================================

    phones = re.findall(
        r'(?<!\d)[6-9]\d{9}(?!\d)',
        text
    )

    phone = ", ".join(
        dict.fromkeys(phones)
    )


    # =================================================
    # EMAIL
    # =================================================

    emails = re.findall(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

    email = ", ".join(
        dict.fromkeys(emails)
    )


    # =================================================
    # GSTIN
    # =================================================

    gstins = re.findall(
        r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9]{2}\b',
        text.upper()
    )

    gstin = ", ".join(
        dict.fromkeys(gstins)
    )


    # =================================================
    # WEBSITE
    # =================================================

    websites = re.findall(
        r'(?:https?://)?(?:www\.)?[A-Za-z0-9-]+\.[A-Za-z]{2,}',
        text
    )

    websites = [
        website
        for website in websites
        if "@" not in website
    ]

    website = ", ".join(
        dict.fromkeys(websites)
    )


    # =================================================
    # DESIGNATION
    # =================================================

    designation = ""

    designation_words = [
        "director",
        "manager",
        "engineer",
        "developer",
        "designer",
        "founder",
        "ceo",
        "cfo",
        "cto",
        "owner",
        "executive",
        "consultant",
        "president",
        "vice president",
        "chairman",
        "secretary",
        "accountant",
        "marketing",
        "sales",
        "hr",
        "technician"
    ]

    for line in lines:

        if any(
            word in line.lower()
            for word in designation_words
        ):

            designation = line
            break


    # =================================================
    # COMPANY
    # =================================================

    company = ""

    company_words = [
        "pvt",
        "private",
        "limited",
        "ltd",
        "solution",
        "solutions",
        "technology",
        "technologies",
        "industries",
        "enterprise",
        "company",
        "corporation",
        "services",
        "systems",
        "group",
        "international"
    ]

    for line in lines:

        if any(
            word in line.lower()
            for word in company_words
        ):

            company = line
            break


    # =================================================
    # PINCODE
    # =================================================

    pincodes = re.findall(
        r'\b\d{6}\b',
        text
    )

    pincode = (
        pincodes[0]
        if pincodes
        else ""
    )


    # =================================================
    # CITY
    # =================================================

    cities = [
        "Pune",
        "Mumbai",
        "Nashik",
        "Nagpur",
        "Thane",
        "Kolhapur",
        "Satara",
        "Sangli",
        "Solapur",
        "Aurangabad",
        "Pimpri",
        "Chinchwad",
        "Delhi",
        "Bangalore",
        "Bengaluru",
        "Hyderabad",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "Surat"
    ]

    city = ""

    for c in cities:

        if c.lower() in text.lower():

            city = c
            break


    # =================================================
    # SR NO
    # =================================================

    sr_match = re.search(
        r'(?:Sr\.?\s*No\.?|S\.?\s*No\.?)\s*[:\-]?\s*(\d+(?:/\d+)?)',
        text,
        re.IGNORECASE
    )

    sr_no = (
        sr_match.group(1)
        if sr_match
        else ""
    )


    # =================================================
    # ADDRESS
    # =================================================

    address_words = [
        "road",
        "street",
        "near",
        "nagar",
        "colony",
        "pune",
        "mumbai",
        "maharashtra",
        "india",
        "shop",
        "floor",
        "building",
        "lane",
        "area",
        "chowk",
        "society",
        "market",
        "park",
        "station",
        "complex"
    ]

    address_lines = []

    for line in lines:

        if any(
            word in line.lower()
            for word in address_words
        ):

            if (
                line != company
                and line != designation
                and "@" not in line
            ):

                address_lines.append(line)

    address = ", ".join(
        address_lines
    )


    # =================================================
    # NAME
    # =================================================

    name = ""

    for line in lines:

        if (
            len(line.split()) >= 2
            and len(line) < 50
            and not re.search(r'\d', line)
            and "@" not in line
            and line != company
            and line != designation
            and not any(
                x in line.lower()
                for x in address_words
            )
            and not any(
                x in line.lower()
                for x in company_words
            )
            and not any(
                x in line.lower()
                for x in designation_words
            )
        ):

            name = line
            break


    # =================================================
    # RETURN DATA
    # =================================================

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


# =====================================================
# SAVE DATA TO NEW CSV + NEW EXCEL
# =====================================================

def save_data(data):

    columns = [
        "Name",
        "Designation",
        "Company",
        "GSTIN",
        "Phone",
        "Email",
        "Website",
        "Address",
        "Sr No",
        "City",
        "Pincode"
    ]

    new_data = pd.DataFrame(
        [data],
        columns=columns
    )

    try:

        # =================================================
        # SAVE NEW CSV
        # =================================================

        if os.path.exists(CSV_FILE):

            old_csv = pd.read_csv(
                CSV_FILE
            )

            final_csv = pd.concat(
                [
                    old_csv,
                    new_data
                ],
                ignore_index=True
            )

        else:

            final_csv = new_data

        final_csv.to_csv(
            CSV_FILE,
            index=False,
            encoding="utf-8-sig"
        )


        # =================================================
        # SAVE NEW EXCEL
        # =================================================

        if os.path.exists(EXCEL_FILE):

            old_excel = pd.read_excel(
                EXCEL_FILE,
                engine="openpyxl"
            )

            final_excel = pd.concat(
                [
                    old_excel,
                    new_data
                ],
                ignore_index=True
            )

        else:

            final_excel = new_data

        final_excel.to_excel(
            EXCEL_FILE,
            index=False,
            engine="openpyxl"
        )


        print()
        print("======================================")
        print("       DATA SAVED SUCCESSFULLY")
        print("======================================")
        print("CSV FILE:")
        print(CSV_FILE)
        print()
        print("EXCEL FILE:")
        print(EXCEL_FILE)
        print("======================================")
        print()

        return True, ""


    except PermissionError:

        return (
            False,
            "Please close the Excel/CSV file and try again."
        )


    except Exception as e:

        print("SAVE ERROR:", str(e))

        return (
            False,
            "Save Error: " + str(e)
        )


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =====================================================
# SCAN CARD
# =====================================================

@app.route(
    "/scan",
    methods=["POST"]
)
def scan():

    # =================================================
    # CHECK IMAGE
    # =================================================

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "message": "Image not received."
        })


    file = request.files["image"]


    # =================================================
    # SAVE TEMP IMAGE
    # =================================================

    try:

        file.save(
            TEMP_FILE
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message":
                "Could not save temporary image: "
                + str(e)
        })


    # =================================================
    # READ IMAGE
    # =================================================

    image = cv2.imread(
        TEMP_FILE
    )

    if image is None:

        return jsonify({
            "success": False,
            "message":
                "Image could not be read."
        })


    # =================================================
    # IMAGE PREPROCESSING
    # =================================================

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )


    # Resize
    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )


    # Reduce noise
    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )


    # Threshold
    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]


    # =================================================
    # OCR
    # =================================================

    try:

        text = pytesseract.image_to_string(
            processed,
            config="--psm 6"
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message":
                "Tesseract OCR error: "
                + str(e)
        })


    # =================================================
    # EXTRACT DATA
    # =================================================

    data = extract_data(
        text
    )


    # =================================================
    # SAVE CSV + EXCEL
    # =================================================

    ok, message = save_data(
        data
    )


    if not ok:

        return jsonify({
            "success": False,
            "message": message
        })


    # =================================================
    # DELETE TEMP IMAGE
    # =================================================

    try:

        if os.path.exists(
            TEMP_FILE
        ):

            os.remove(
                TEMP_FILE
            )

    except Exception:

        pass


    # =================================================
    # RETURN RESULT
    # =================================================

    return jsonify({

        "success": True,

        "data": data,

        "raw_text": text,

        "message":
            "Data saved successfully to new CSV and Excel file."

    })


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("     BUSINESS CARD OCR SCANNER")
    print("======================================")
    print()
    print("NEW CSV:")
    print(CSV_FILE)
    print()
    print("NEW EXCEL:")
    print(EXCEL_FILE)
    print()
    print("OPEN:")
    print("http://127.0.0.1:5000")
    print()
    print("======================================")


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )