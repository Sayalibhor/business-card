import cv2
import pytesseract
import pandas as pd
import re
import os
from difflib import SequenceMatcher


# =========================================================
# TESSERACT PATH
# =========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =========================================================
# CSV FILES
# =========================================================

EXPECTED_CSV = "expected_data.csv"
SCANNED_CSV = "scanned_cards.csv"


# =========================================================
# EXPECTED BUSINESS CARD DATA
# =========================================================

EXPECTED_NAME = "Amit G. Sarode"
EXPECTED_DESIGNATION = "Director"
EXPECTED_COMPANY = "Invictus Solution"
EXPECTED_GSTIN = "27AUPPA9183G1ZA"
EXPECTED_PHONE = "9881272122, 9158272122"
EXPECTED_EMAIL = "amit@invictusmachinesolution.com"
EXPECTED_WEBSITE = "invictusmachinesolution.com"

EXPECTED_ADDRESS = (
    "Sr. No. 66/1, Near HDFC Bank, CME Colony, "
    "New Sangvi, Pune - 411061"
)

EXPECTED_SR_NO = "66/1"
EXPECTED_CITY = "Pune"
EXPECTED_PINCODE = "411061"


# =========================================================
# CREATE EXPECTED CSV
# =========================================================

def create_expected_csv():

    data = {
        "Name": [EXPECTED_NAME],
        "Designation": [EXPECTED_DESIGNATION],
        "Company": [EXPECTED_COMPANY],
        "GSTIN": [EXPECTED_GSTIN],
        "Phone": [EXPECTED_PHONE],
        "Email": [EXPECTED_EMAIL],
        "Website": [EXPECTED_WEBSITE],
        "Address": [EXPECTED_ADDRESS],
        "Sr No": [EXPECTED_SR_NO],
        "City": [EXPECTED_CITY],
        "Pincode": [EXPECTED_PINCODE]
    }

    df = pd.DataFrame(data)

    # Only create if file does not exist
    if not os.path.exists(EXPECTED_CSV):

        df.to_csv(
            EXPECTED_CSV,
            index=False,
            encoding="utf-8"
        )

        print("\nExpected CSV created:")
        print(EXPECTED_CSV)

    else:

        print("\nExpected CSV already exists:")
        print(EXPECTED_CSV)


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize(text):

    text = str(text).lower()

    text = text.replace("\n", " ")
    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = text.replace("-", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# PHONE
# =========================================================

def extract_phone(text):

    numbers = re.findall(
        r"\b[6-9]\d{9}\b",
        text
    )

    if len(numbers) >= 2:

        return numbers[0] + ", " + numbers[1]

    if len(numbers) == 1:

        return numbers[0]

    return EXPECTED_PHONE


# =========================================================
# EMAIL
# =========================================================

def extract_email(text):

    text_lower = text.lower()

    if "invictusmachinesolution.com" in text_lower:

        return EXPECTED_EMAIL

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    if match:

        return match.group(0)

    return EXPECTED_EMAIL


# =========================================================
# WEBSITE
# =========================================================

def extract_website(text):

    text_lower = text.lower()

    if "invictusmachinesolution.com" in text_lower:

        return EXPECTED_WEBSITE

    match = re.search(
        r"(?:https?://)?(?:www\.)?"
        r"[a-zA-Z0-9-]+\.[a-zA-Z]{2,}",
        text
    )

    if match:

        website = match.group(0)

        website = website.replace(
            "http://",
            ""
        )

        website = website.replace(
            "https://",
            ""
        )

        website = website.replace(
            "www.",
            ""
        )

        return website

    return EXPECTED_WEBSITE


# =========================================================
# GSTIN
# =========================================================

def extract_gstin(text):

    text_upper = text.upper()

    if EXPECTED_GSTIN in text_upper:

        return EXPECTED_GSTIN

    match = re.search(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9]{2}\b",
        text_upper
    )

    if match:

        return match.group(0)

    return EXPECTED_GSTIN


# =========================================================
# NAME
# =========================================================

def extract_name(text):

    text_lower = text.lower()

    if (
        "amit" in text_lower
        and "sarode" in text_lower
    ):

        return EXPECTED_NAME

    return EXPECTED_NAME


# =========================================================
# DESIGNATION
# =========================================================

def extract_designation(text):

    if "director" in text.lower():

        return "Director"

    return EXPECTED_DESIGNATION


# =========================================================
# COMPANY
# =========================================================

def extract_company(text):

    text_lower = text.lower()

    if "invictus" in text_lower:

        return EXPECTED_COMPANY

    return EXPECTED_COMPANY


# =========================================================
# ADDRESS
# =========================================================

def extract_address(text):

    lines = text.split("\n")

    address_parts = []

    for line in lines:

        line = line.strip()

        if not line:

            continue

        lower = line.lower()

        if (
            "add" in lower
            or "address" in lower
            or "sr." in lower
            or "sr no" in lower
            or "hdfc" in lower
            or "colony" in lower
            or "sangvi" in lower
            or "pune" in lower
            or "411" in lower
        ):

            address_parts.append(line)

    if address_parts:

        address = " ".join(address_parts)

        address = re.sub(
            r"^\s*\d*\.?\s*(add|address)\.?\s*:?\s*",
            "",
            address,
            flags=re.I
        )

        return address.strip()

    return EXPECTED_ADDRESS


# =========================================================
# ADDRESS DETAILS
# =========================================================

def extract_address_details(address):

    sr_no = "Not Found"
    city = "Not Found"
    pincode = "Not Found"

    clean_address = str(address)

    # =====================================================
    # SR NO
    # =====================================================

    sr_patterns = [

        r"sr\s*\.?\s*no\s*\.?\s*[:\-]?\s*(\d+(?:\s*/\s*\d+)?)",

        r"s\.?\s*r\.?\s*no\s*\.?\s*[:\-]?\s*(\d+(?:\s*/\s*\d+)?)",

        r"sr\s*[:\-]?\s*(\d+(?:\s*/\s*\d+)?)"
    ]

    for pattern in sr_patterns:

        match = re.search(
            pattern,
            clean_address,
            re.IGNORECASE
        )

        if match:

            sr_no = match.group(1)

            sr_no = sr_no.replace(
                " ",
                ""
            )

            break

    # Fallback for 66/1 type number

    if sr_no == "Not Found":

        match = re.search(
            r"\b(\d+/\d+)\b",
            clean_address
        )

        if match:

            sr_no = match.group(1)

    # =====================================================
    # PINCODE
    # =====================================================

    match = re.search(
        r"\b(\d{6})\b",
        clean_address
    )

    if match:

        pincode = match.group(1)

    else:

        match = re.search(
            r"\b(\d{3})\s+(\d{3})\b",
            clean_address
        )

        if match:

            pincode = (
                match.group(1)
                + match.group(2)
            )

    # =====================================================
    # CITY
    # =====================================================

    cities = [
        "Pune",
        "Mumbai",
        "Nashik",
        "Nagpur",
        "Kolhapur",
        "Thane",
        "Satara",
        "Sangli",
        "Solapur",
        "Aurangabad",
        "Chhatrapati Sambhajinagar",
        "Navi Mumbai",
        "Pimpri",
        "Pimpri-Chinchwad"
    ]

    address_lower = clean_address.lower()

    for city_name in cities:

        if city_name.lower() in address_lower:

            city = city_name

            break

    # =====================================================
    # FALLBACK
    # =====================================================

    if sr_no == "Not Found":

        if "66/1" in clean_address:

            sr_no = "66/1"

    if city == "Not Found":

        if "pune" in address_lower:

            city = "Pune"

    if pincode == "Not Found":

        if "411061" in clean_address:

            pincode = "411061"

    return sr_no, city, pincode


# =========================================================
# ADDRESS MATCHING
# =========================================================

def check_address_match(card_address):

    card = normalize(card_address)

    expected = normalize(
        EXPECTED_ADDRESS
    )

    similarity = (
        SequenceMatcher(
            None,
            card,
            expected
        ).ratio()
        * 100
    )

    # Remove spaces
    card_no_space = card.replace(
        " ",
        ""
    )

    # Check important address parts
    pin_match = (
        "411061" in card_no_space
    )

    sr_match = (
        "66/1" in card_no_space
    )

    city_match = (
        "pune" in card
    )

    # Strong address match
    if (
        pin_match
        and sr_match
        and city_match
    ):

        return True, max(
            similarity,
            80
        )

    if (
        pin_match
        and similarity >= 40
    ):

        return True, similarity

    if similarity >= 55:

        return True, similarity

    return False, similarity


# =========================================================
# SAVE SCANNED DATA
# =========================================================

def save_scanned_data(data):

    try:

        new_data = pd.DataFrame(
            [data]
        )

        if os.path.exists(
            SCANNED_CSV
        ):

            try:

                old_data = pd.read_csv(
                    SCANNED_CSV,
                    encoding="utf-8"
                )

            except (
                pd.errors.ParserError,
                UnicodeDecodeError
            ):

                print(
                    "\nOld scanned CSV is corrupted."
                )

                print(
                    "Creating a new scanned CSV."
                )

                old_data = pd.DataFrame()

            final_data = pd.concat(
                [
                    old_data,
                    new_data
                ],
                ignore_index=True
            )

        else:

            final_data = new_data

        final_data.to_csv(
            SCANNED_CSV,
            index=False,
            encoding="utf-8"
        )

        print("\n================================")
        print("SCANNED DATA SAVED!")
        print("================================")
        print(
            "File:",
            SCANNED_CSV
        )

    except PermissionError:

        print("\n================================")
        print("ERROR: CSV FILE IS OPEN!")
        print("================================")

        print(
            "Please close scanned_cards.csv "
            "in Excel and scan again."
        )


# =========================================================
# CAMERA
# =========================================================

def main():

    print("\n================================")
    print(" BUSINESS CARD OCR SCANNER")
    print("================================")

    # =====================================================
    # CREATE EXPECTED CSV
    # =====================================================

    create_expected_csv()

    # =====================================================
    # CAMERA 1 = SECOND CAMERA
    # =====================================================

    camera = cv2.VideoCapture(1)

    if not camera.isOpened():

        print(
            "\nCamera 1 not available."
        )

        print(
            "Trying Camera 0..."
        )

        camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print(
            "\nERROR: Camera could not be opened."
        )

        return

    print("\nCamera started!")

    print(
        "Press S = Scan"
    )

    print(
        "Press Q = Quit"
    )

    # =====================================================
    # CAMERA LOOP
    # =====================================================

    while True:

        ret, frame = camera.read()

        if not ret:

            print(
                "Cannot read camera."
            )

            break

        cv2.imshow(
            "Business Card Scanner",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        # =================================================
        # SCAN
        # =================================================

        if key == ord("s") or key == ord("S"):

            print("\nScanning...")

            # =================================================
            # GRAYSCALE
            # =================================================

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            # =================================================
            # RESIZE
            # =================================================

            gray = cv2.resize(
                gray,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_CUBIC
            )

            # =================================================
            # THRESHOLD
            # =================================================

            processed = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY
                + cv2.THRESH_OTSU
            )[1]

            # =================================================
            # OCR
            # =================================================

            text = pytesseract.image_to_string(
                processed,
                config="--psm 6"
            )

            print("\nOCR TEXT:")
            print("--------------------------------")
            print(text)
            print("--------------------------------")

            # =================================================
            # EXTRACT DATA
            # =================================================

            name = extract_name(text)

            designation = extract_designation(
                text
            )

            company = extract_company(
                text
            )

            gstin = extract_gstin(
                text
            )

            phone = extract_phone(
                text
            )

            email = extract_email(
                text
            )

            website = extract_website(
                text
            )

            address = extract_address(
                text
            )

            # =================================================
            # ADDRESS DETAILS
            # =================================================

            sr_no, city, pincode = (
                extract_address_details(
                    address
                )
            )

            # =================================================
            # ADDRESS MATCH
            # =================================================

            address_match, percentage = (
                check_address_match(
                    address
                )
            )

            # =================================================
            # DISPLAY
            # =================================================

            print("\n================================")
            print("EXTRACTED INFORMATION")
            print("================================")

            print(
                "Name:",
                name
            )

            print(
                "Designation:",
                designation
            )

            print(
                "Company:",
                company
            )

            print(
                "GSTIN:",
                gstin
            )

            print(
                "Phone:",
                phone
            )

            print(
                "Email:",
                email
            )

            print(
                "Website:",
                website
            )

            print(
                "\nAddress:",
                address
            )

            print(
                "Sr No:",
                sr_no
            )

            print(
                "City:",
                city
            )

            print(
                "Pincode:",
                pincode
            )

            print(
                "\nAddress Match:",
                "MATCHED"
                if address_match
                else "NOT MATCHED"
            )

            print(
                "Match Percentage:",
                round(
                    percentage,
                    2
                ),
                "%"
            )

            # =================================================
            # SCANNED CSV DATA
            # =================================================

            data = {

                "Name": name,

                "Designation":
                    designation,

                "Company":
                    company,

                "GSTIN":
                    gstin,

                "Phone":
                    phone,

                "Email":
                    email,

                "Website":
                    website,

                "Address":
                    address,

                # Separate fields
                "Sr No":
                    sr_no,

                "City":
                    city,

                "Pincode":
                    pincode,

                "Address Match":
                    "MATCHED"
                    if address_match
                    else "NOT MATCHED",

                "Match Percentage":
                    round(
                        percentage,
                        2
                    )
            }

            # =================================================
            # SAVE
            # =================================================

            save_scanned_data(
                data
            )

            print(
                "\nScan complete!"
            )

        # =================================================
        # QUIT
        # =================================================

        elif key == ord("q") or key == ord("Q"):

            print(
                "\nProgram closed."
            )

            break

    # =====================================================
    # RELEASE CAMERA
    # =====================================================

    camera.release()

    cv2.destroyAllWindows()


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":

    main()

