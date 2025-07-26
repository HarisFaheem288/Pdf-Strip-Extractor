import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import os
import io
import base64
import re
from tempfile import TemporaryDirectory

st.set_page_config(page_title="PDF Strip Extractor", layout="centered")
st.title("📄 Dossier PDF Strip Extractor")
st.write("Upload your Dossier PDF. It will extract each strip (based on LO/LA headers) into a separate PDF file.")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

def extract_strips_from_pdf_bytes(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        st.error(f"❌ Failed to open PDF: {str(e)}")
        return []

    THRESHOLD = 15  # Minimum y-distance between headers to treat them as separate strips

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        starts = []

        # Detect lines containing LO/LA headers
        for b in blocks:
            for l in b.get("lines", []):
                line_text = " ".join([s["text"] for s in l["spans"]]).strip()
                if re.search(r'\bL[O0A]\b', line_text.upper()):
                    y = l["bbox"][1]
                    match = re.search(r'\bL[O0A]\b\s+(\S+)', line_text.upper())
                    dossier = match.group(1) if match else "Unknown"
                    starts.append({"y_start": y, "dossier": dossier})

        starts.sort(key=lambda x: x["y_start"])
        filtered_starts = []
        for s in starts:
            if not filtered_starts or abs(s["y_start"] - filtered_starts[-1]["y_start"]) > THRESHOLD:
                filtered_starts.append(s)

        if not filtered_starts:
            st.warning(f"⚠️ No headers found on page {page_num + 1}")
            continue

        cut_points = [s["y_start"] for s in filtered_starts]
        cut_points.append(page.rect.height)

        for i in range(len(filtered_starts)):
            y0 = cut_points[i]
            y1 = cut_points[i+1]

            if y1 <= y0:
                continue

            rect = fitz.Rect(0, y0, page.rect.width, y1)
            pix = page.get_pixmap(clip=rect, dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))

            row = str(i + 1)
            dossier = filtered_starts[i]["dossier"]
            filename = f"{dossier}-{row}.pdf"
            output_path = os.path.join(output_dir, filename)

            img.save(output_path, "PDF", resolution=300.0)

            with open(output_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            result.append({
                "filename": filename,
                "filedata": encoded
            })

            st.success(f"✅ Extracted: {filename}")

    doc.close()
    return result

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    with TemporaryDirectory() as tmpdir:
        with st.spinner("🔍 Extracting strips..."):
            results = extract_strips_from_pdf_bytes(pdf_bytes, tmpdir)

        if results:
            st.success(f"🎉 Done! Extracted {len(results)} strips.")
            for idx, r in enumerate(results):
                st.download_button(
                    label=f"📥 Download {r['filename']}",
                    data=base64.b64decode(r["filedata"]),
                    file_name=r["filename"],
                    mime="application/pdf",
                    key=f"download_{idx}"
                )
        else:
            st.error("⚠️ No strips found.")
