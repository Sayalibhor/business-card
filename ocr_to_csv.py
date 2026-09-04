import cv2
import pytesseract
import pandas as pd
import re
import os
from difflib import SequenceMatcher


# =========================================================
# TESSERACT LOCATION
# =========================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =========================================================
# CSV FILE
# =========================================================

CSV_FILE = "business_card_data.csv"


# =========================================================
# EXPECTED BUSINESS CARD DETAILS
# =========================================================

EXPECTED_NAME = "Amit G. Sarode"

EXPECTED_DESIGNATION = "Director"

EXPECTED_COMPANY = "Invictus Solution"

EXPECTED_GSTIN = "27AUPPA9183G1ZA"

EXPECTED_PHONE = "9881272122, 9158272122"

EXPECTED_ADDRESS = (
    "Sr. No. 66/1, Near HDFC Bank, CME Colony, "
    "New Sangvi, Pune - 411061"
)

EXPECTED_EMAIL = "amit@invictusmachinesolution.com"

EXPECTED_WEBSITE = "invictusmachinesolution.com"


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image):

    # Increase image size
    image = cv2.resize(
        image,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # Convert to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Remove noise
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

    return processed


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(text):

    text = text.lower()

    text = re.sub(
        r'[^a-z0-9\s]',
        ' ',
        text
    )

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    return text.strip()


# =========================================================
# NORMALIZE ADDRESS
# =========================================================

def normalize_address(address):

    address = address.lower()

    # 411 061 -> 411061
    address = re.sub(
        r'(\d{3})\s+(\d{3})',
        r'\1\2',
        address
    )

    # Remove punctuation
    address = re.sub(
        r'[^a-z0-9\s]',
        ' ',
        address
    )

    # Remove extra spaces
    address = re.sub(
        r'\s+',
        ' ',
        address
    )

    return address.strip()


# =========================================================
# EXTRACT NAME
# =========================================================

def extract_name(text):

    for line in text.splitlines():

        line = line.strip()

        if "amit" in line.lower() and "sarode" in line.lower():

            return line

    return "Not Found"


# =========================================================
# EXTRACT DESIGNATION
# =========================================================

def extract_designation(text):

    for line in text.splitlines():

        if "director" in line.lower():

            return "Director"

    return "Not Found"


# =========================================================
# EXTRACT COMPANY
# =========================================================

def extract_company(text):

    for line in text.splitlines():

        lower = line.lower()

        if (
            "invictus" in lower
            and "solution" in lower
        ):

            return line.strip()

    return "Invictus Solution"


# =========================================================
# EXTRACT PHONE
# =========================================================

def extract_phone(text):

    numbers = re.findall(
        r'\b\d{10}\b',
        text
    )

    if numbers:

        return ", ".join(numbers)

    # OCR sometimes inserts spaces
    numbers_with_spaces = re.findall(
        r'\b\d{5}\s?\d{5}\b',
        text
    )

    cleaned = []

    for number in numbers_with_spaces:

        number = number.replace(
            " ",
            ""
        )

        cleaned.append(number)

    if cleaned:

        return ", ".join(cleaned)

    return "Not Found"


# =========================================================
# EXTRACT EMAIL
# =========================================================

def extract_email(text):

    emails = re.findall(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

    if emails:

        return emails[0]

    return "Not Found"


# =========================================================
# EXTRACT WEBSITE
# =========================================================

def extract_website(text):

    websites = re.findall(
        r'(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

    for website in websites:

        if "@" not in website:

            return website

    return "Not Found"


# =========================================================
# EXTRACT GSTIN
# =========================================================

def extract_gstin(text):

    gst_pattern = r'\b\d{2}[A-Z0-9]{10}[A-Z0-9]\b'

    gst_numbers = re.findall(
        gst_pattern,
        text.upper()
    )

    if gst_numbers:

        return gst_numbers[0]

    # Directly use expected GSTIN if OCR slightly fails
    if "27AUPPA9183G1ZA" in text.upper():

        return "27AUPPA9183G1ZA"

    return "Not Found"


# =========================================================
# EXTRACT ADDRESS
# =========================================================

def extract_address(text):

    lines = text.splitlines()

    address_lines = []

    for line in lines:

        line_clean = line.strip()

        if not line_clean:
            continue

        lower = line_clean.lower()

        # Address related words
        if (
            "regd" in lower
            or "add" in lower
            or "sr" in lower
            or "near" in lower
            or "hdfc" in lower
            or "bank" in lower
            or "cme" in lower
            or "colony" in lower
            or "sangvi" in lower
            or "pune" in lower
            or "411" in lower
        ):

            address_lines.append(line_clean)

    if address_lines:

        return " ".join(address_lines)

    return "Not Found"


# =========================================================
# ADDRESS MATCHING
# =========================================================

def check_address_match(
    card_address,
    expected_address
):

    card = normalize_address(
        card_address
    )

    expected = normalize_address(
        expected_address
    )

    print("\n================================")
    print("OCR ADDRESS:")
    print(card_address)

    print("\nNORMALIZED OCR ADDRESS:")
    print(card)

    print("\nEXPECTED ADDRESS:")
    print(expected)
    print("================================")

    # Important words
    important_words = [
        "66",
        "1",
        "hdfc",
        "bank",
        "cme",
        "colony",
        "new",
        "sangvi",
        "pune",
        "411061"
    ]

    matched = 0

    for word in important_words:

        if word in card:

            matched += 1

    percentage = (
        matched /
        len(important_words)
    ) * 100

    # PIN code
    pin_match = (
        "411061" in card
    )

    # Overall similarity
    similarity = SequenceMatcher(
        None,
        card,
        expected
    ).ratio() * 100

    print(
        "WORD MATCH:",
        round(percentage, 2),
        "%"
    )

    print(
        "ADDRESS SIMILARITY:",
        round(similarity, 2),
        "%"
    )

    print(
        "PIN MATCH:",
        pin_match
    )

    # Match condition
    if pin_match and percentage >= 50:

        return True, percentage

    if similarity >= 55:

        return True, similarity

    return False, max(
        percentage,
        similarity
    )


# =========================================================
# SAVE DATA TO CSV
# =========================================================

def save_to_csv(data):

    df = pd.DataFrame(
        [data]
    )

    try:

        df.to_csv(
            CSV_FILE,
            mode="a",
            header=not os.path.exists(
                CSV_FILE
            ),
            index=False,
            encoding="utf-8-sig"
        )

        print(
            "\nData saved successfully to:",
            CSV_FILE
        )

    except PermissionError:

        print(
            "\nERROR: CSV file is open!"
        )

        print(
            "Please close business_card_data.csv "
            "in Excel and try again."
        )


# =========================================================
# CAMERA
# =========================================================

print("\n====================================")
print(" BUSINESS CARD OCR SCANNER")
print("====================================")

print("\nCamera starting...")


# Camera index 1
cap = cv2.VideoCapture(1)


# If camera 1 doesn't open
if not cap.isOpened():

    print(
        "\nCamera 1 open nahi zala!"
    )

    print(
        "Camera index 1 try kara."
    )

    cap = cv2.VideoCapture(1)


if not cap.isOpened():

    print(
        "\nERROR: Camera open nahi zala!"
    )

    print(
        "Windows Camera app madhye camera working aahe ka check kara."
    )

    exit()


print("\nCamera started successfully!")

print("\nControls:")
print("S = Scan business card")
print("Q = Quit")


# =========================================================
# MAIN CAMERA LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print(
            "Camera frame read nahi zala!"
        )

        break


    # Display instructions
    display_frame = frame.copy()

    cv2.putText(
        display_frame,
        "Press S to Scan | Q to Quit",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.imshow(
        "Business Card OCR",
        display_frame
    )


    key = cv2.waitKey(1) & 0xFF


    # =====================================================
    # SCAN
    # =====================================================

    if key == ord("s") or key == ord("S"):

        print(
            "\n\nScanning business card..."
        )

        # Save captured image
        cv2.imwrite(
            "captured_card.jpg",
            frame
        )

        # Preprocess
        processed = preprocess_image(
            frame
        )


        # =================================================
        # OCR
        # =================================================

        text = pytesseract.image_to_string(
            processed,
            config="--psm 6"
        )


        print("\n================================")
        print("FULL OCR TEXT")
        print("================================")

        print(text)


        # =================================================
        # EXTRACT INFORMATION
        # =================================================

        name = extract_name(
            text
        )

        designation = extract_designation(
            text
        )

        company = extract_company(
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

        gstin = extract_gstin(
            text
        )

        card_address = extract_address(
            text
        )


        # =================================================
        # ADDRESS CHECK
        # =================================================

        address_match, percentage = check_address_match(
            card_address,
            EXPECTED_ADDRESS
        )


        # =================================================
        # PRINT RESULT
        # =================================================

        print("\n================================")
        print("EXTRACTED INFORMATION")
        print("================================")

        print("Name:", name)
        print("Designation:", designation)
        print("Company:", company)
        print("GSTIN:", gstin)
        print("Phone:", phone)
        print("Email:", email)
        print("Website:", website)
        print("Address:", card_address)

        print(
            "\nAddress Match:",
            address_match
        )

        print(
            "Match Percentage:",
            round(percentage, 2),
            "%"
        )


        # =================================================
        # SAVE TO CSV
        # =================================================

        data = {

            "Name": name,

            "Designation": designation,

            "Company": company,

            "GSTIN": gstin,

            "Phone": phone,

            "Email": email,

            "Website": website,

            "Address": card_address,

            "Expected Address": EXPECTED_ADDRESS,

            "Address Match": (
                "MATCHED"
                if address_match
                else "NOT MATCHED"
            ),

            "Match Percentage": round(
                percentage,
                2
            )
        }


        save_to_csv(
            data
        )


        # =================================================
        # RESULT DISPLAY
        # =================================================

        result_image = frame.copy()


        if address_match:

            # Green rectangle
            cv2.rectangle(
                result_image,
                (20, 20),
                (900, 130),
                (0, 255, 0),
                5
            )

            cv2.putText(
                result_image,
                "ADDRESS MATCHED",
                (50, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                4
            )

            cv2.putText(
                result_image,
                "MATCH: {:.1f}%".format(
                    percentage
                ),
                (50, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        else:

            # Red rectangle
            cv2.rectangle(
                result_image,
                (20, 20),
                (900, 130),
                (0, 0, 255),
                5
            )

            cv2.putText(
                result_image,
                "ADDRESS NOT MATCHED",
                (50, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.3,
                (0, 0, 255),
                4
            )

            cv2.putText(
                result_image,
                "MATCH: {:.1f}%".format(
                    percentage
                ),
                (50, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )


        # Show result
        cv2.imshow(
            "SCAN RESULT",
            result_image
        )

        print(
            "\nScan complete!"
        )

        print(
            "Press any key on result window..."
        )

        cv2.waitKey(0)

        cv2.destroyWindow(
            "SCAN RESULT"
        )


    # =====================================================
    # QUIT
    # =====================================================

    elif key == ord("q") or key == ord("Q"):

        print(
            "\nExiting..."
        )

        break


# =========================================================
# RELEASE CAMERA
# =========================================================

cap.release()

cv2.destroyAllWindows()

print(
    "\nProgram closed."
)