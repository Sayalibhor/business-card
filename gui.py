import cv2
import pytesseract
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import re
import os

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

EXCEL = "scanned_cards.xlsx"
cap = None
frame = None


# ---------- OCR DATA EXTRACTION ----------

def extract_data(text):

    lines = [x.strip() for x in text.split("\n") if x.strip()]

    # Phone
    phones = re.findall(r"(?<!\d)[6-9]\d{9}(?!\d)", text)

    # Email
    emails = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    # Website
    websites = re.findall(
        r"(?:https?://)?(?:www\.)?[A-Za-z0-9-]+\.[A-Za-z]{2,}",
        text
    )

    websites = [
        x for x in websites
        if "@" not in x
    ]

    # GSTIN
    gst = re.findall(
        r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9]{2}\b",
        text.upper()
    )

    # Designation
    designation = ""
    jobs = [
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
        "sales manager",
        "marketing manager"
    ]

    for line in lines:
        for job in jobs:
            if job.lower() in line.lower():
                designation = line
                break
        if designation:
            break

    # Company
    company = ""
    company_words = [
        "pvt",
        "private limited",
        "ltd",
        "limited",
        "solutions",
        "solution",
        "technologies",
        "technology",
        "industries",
        "enterprise"
    ]

    for line in lines:
        if any(x in line.lower() for x in company_words):
            company = line
            break

    # Address
    address_lines = []

    address_words = [
        "address",
        "road",
        "street",
        "near",
        "nagar",
        "colony",
        "pune",
        "mumbai",
        "maharashtra",
        "india",
        "411",
        "shop",
        "floor",
        "building"
    ]

    for line in lines:
        if any(x in line.lower() for x in address_words):
            address_lines.append(line)

    address = " ".join(address_lines)

    # City
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
        "Chinchwad"
    ]

    city = ""

    for c in cities:
        if c.lower() in text.lower():
            city = c
            break

    # Pincode
    pins = re.findall(r"\b\d{6}\b", text)

    # Sr No
    sr = re.findall(
        r"(?:Sr\.?\s*No\.?|S\.?\s*No\.?)\s*[:\-]?\s*(\d+(?:/\d+)?)",
        text,
        re.I
    )

    # Name
    name = ""

    # First suitable line which is not contact/address information
    for line in lines:

        low = line.lower()

        if (
            "@" not in line
            and not re.search(r"\d{10}", line)
            and not re.search(r"\d{6}", line)
            and not any(x in low for x in address_words)
            and not any(x in low for x in company_words)
            and not any(x in low for x in jobs)
            and len(line.split()) >= 2
            and len(line) < 50
        ):
            name = line
            break

    return {
        "Name": name,
        "Designation": designation,
        "Company": company,
        "GSTIN": gst[0] if gst else "",
        "Phone": ", ".join(phones),
        "Email": emails[0] if emails else "",
        "Website": websites[0] if websites else "",
        "Address": address,
        "Sr No": sr[0] if sr else "",
        "City": city,
        "Pincode": pins[0] if pins else ""
    }


# ---------- CAMERA ----------

def start_camera():

    global cap

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        messagebox.showerror(
            "Error",
            "Camera not found"
        )
        return

    show_camera()


def show_camera():

    global frame

    if cap is None:
        return

    ret, frame = cap.read()

    if ret:

        img = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        img = cv2.resize(
            img,
            (650, 380)
        )

        photo = ImageTk.PhotoImage(
            Image.fromarray(img)
        )

        camera_label.config(
            image=photo
        )

        camera_label.image = photo

    root.after(
        10,
        show_camera
    )


# ---------- SCAN ----------

def scan_card():

    if frame is None:

        messagebox.showwarning(
            "Warning",
            "Start camera first"
        )

        return

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    # Increase image size
    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # Improve text
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

    # Save Excel
    new = pd.DataFrame([data])

    if os.path.exists(EXCEL):

        old = pd.read_excel(EXCEL)

        new = pd.concat(
            [old, new],
            ignore_index=True
        )

    new.to_excel(
        EXCEL,
        index=False
    )

    # Show result
    result.delete(
        "1.0",
        tk.END
    )

    for key, value in data.items():

        result.insert(
            tk.END,
            f"{key}: {value}\n"
        )

    messagebox.showinfo(
        "Success",
        "Business card data saved in Excel!"
    )


# ---------- EXIT ----------

def exit_app():

    if cap:
        cap.release()

    root.destroy()


# ---------- GUI ----------

root = tk.Tk()

root.title(
    "Business Card OCR Scanner"
)

root.geometry(
    "750x650"
)

tk.Label(
    root,
    text="BUSINESS CARD OCR SCANNER",
    font=("Arial", 20, "bold")
).pack(pady=10)

camera_label = tk.Label(root)

camera_label.pack()

tk.Button(
    root,
    text="Start Camera",
    command=start_camera,
    width=25
).pack(pady=5)

tk.Button(
    root,
    text="Scan & Save to Excel",
    command=scan_card,
    width=25
).pack(pady=5)

tk.Button(
    root,
    text="Exit",
    command=exit_app,
    width=25
).pack(pady=5)

result = tk.Text(
    root,
    height=10,
    width=85
)

result.pack(pady=10)

root.mainloop()