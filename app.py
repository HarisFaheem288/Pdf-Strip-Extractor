import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import io
import base64
import re
import zipfile
import os
from tempfile import TemporaryDirectory

# Optional: Set path for tesseract if on Windows
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="PDF Strip Extractor", layout="centered")

st.title("📄 PDF Strip Extractor with Dossier Number Detection")
st.markdown("Upload a PDF, and this app will extract each strip with dossier numbers using OCR (Tesseract).")

# Function to preprocess image for better OCR
def preprocess_image(image):
    image = ImageOps.grayscale(image)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(2.5)

# Function to extract dossier headers
def extract_dossier_headers(image, page_num, image_height):
    image = preprocess_image(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config='--psm 6')
    headers = []
    seen_y = set()

    for i, word in enumerate(data['text']):
        word = word.strip().upper()
        if word in ['LO', 'LA', 'L0'] and i + 1 < len(data['text']):
            next_word = data['text'][i + 1].strip()
            y = data['top'][i]

            if any(abs(y - sy) < 10 for sy in seen_y):
                continue
            seen_y.add(y)

            if re.fullmatch(r'\d+', next_word):
                headers.append((y, next_word))
            else:
                headers.append((y, f"Unknown_{page_num}_{i}"))

    return sorted(headers, key=lambda x: x[0])

# Function to extract strips from PDF
def extract_strips_from_pdf(pdf_bytes):
    result = []
    MIN_HEIGHT = 50  # pixels

    with TemporaryDirectory() as output_dir:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(dpi=300)
            image = Image.open(io.BytesIO(pix.tobytes()))
            headers = extract_dossier_headers(image, page_num, image.height)

            if not headers:
                st.warning(f"No headers found on page {page_num + 1}")
                continue

            cut_points = headers.copy()
            last_y = cut_points[-1][0]
            if (image.height - last_y) > (MIN_HEIGHT + 20) and "Unknown" not in cut_points[-1][1]:
                cut_points.append((image.height, "END"))

            for i in range(len(cut_points) - 1):
                y0 = cut_points[i][0]
                y1 = cut_points[i + 1][0]
                dossier = cut_points[i][1]

                height = y1 - y0
                if height < MIN_HEIGHT or y1 <= y0:
                    continue

                rect = (0, y0, image.width, y1)
                cropped = image.crop(rect)

                if "Unknown" in dossier :
                    continue  # Skip last unknown if all others are valid

                filename = f"{dossier}_{i+1}.pdf"
                output_path = os.path.join(output_dir, filename)
                cropped.save(output_path, "PDF", resolution=300.0)

                with open(output_path, "rb") as f:
                    file_bytes = f.read()
                    result.append((filename, file_bytes))

                st.success(f"✅ Extracted: {filename}")

        doc.close()
    return result

# Streamlit UI
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    with st.spinner("Extracting strips..."):
        strips = extract_strips_from_pdf(pdf_bytes)

    if strips:
        st.markdown("---")
        st.subheader("🧾 Extracted Strips")
        for filename, filedata in strips:
            st.download_button(
                label=f"📥 Download {filename}",
                data=filedata,
                file_name=filename,
                mime="application/pdf"
            )

        # Option to download all as ZIP
        with io.BytesIO() as zip_buffer:
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for filename, filedata in strips:
                    zip_file.writestr(filename, filedata)
            zip_buffer.seek(0)
            st.download_button("📦 Download All as ZIP", data=zip_buffer, file_name="all_strips.zip", mime="application/zip")
    else:
        st.error("No strips extracted.")
