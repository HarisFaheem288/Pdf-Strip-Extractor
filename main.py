'''import fitz  # PyMuPDF
from PIL import Image
import os
import io
import base64
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from tempfile import TemporaryDirectory

app = FastAPI()

class PDFBase64Request(BaseModel):
    pdf_base64: str

def extract_strips_from_pdf_bytes(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num, page in enumerate(doc):
        words = page.get_text("words")
        starts = []

        for i, word in enumerate(words):
            text = word[4]
            # Match LO / LA / L0 as header keywords
            if re.fullmatch(r'L[O0A]', text.upper()):
                y_start = word[1]
                dossier = words[i+1][4] if i + 1 < len(words) else "Unknown"
                row = str(len(starts) + 1)
                starts.append({'y_start': y_start, 'dossier': dossier, 'row': row})

        starts.sort(key=lambda x: x['y_start'])

        if not starts:
            print(f"⚠️ No headers found on page {page_num + 1}")
            continue

        # Define cutting positions (from header to next or page bottom)
        cut_points = [s['y_start'] for s in starts]
        cut_points.append(page.rect.height)

        for i in range(len(starts)):
            y0 = cut_points[i]
            y1 = cut_points[i+1]

            if y1 <= y0:
                continue

            rect = fitz.Rect(0, y0, page.rect.width, y1)
            pix = page.get_pixmap(clip=rect, dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))

            filename = f"{starts[i]['dossier']}-{starts[i]['row']}.pdf"
            output_path = os.path.join(output_dir, filename)

            img.save(output_path, "PDF", resolution=300.0)

            with open(output_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            result.append({
                "filename": filename,
                "filedata": encoded
            })

            print(f"✅ Saved: {filename} from Y={int(y0)} to Y={int(y1)}")

    doc.close()
    return result

@app.post("/extract")
async def extract_from_base64_pdf(request: PDFBase64Request):
    try:
        pdf_bytes = base64.b64decode(request.pdf_base64)
        with TemporaryDirectory() as tmpdir:
            result = extract_strips_from_pdf_bytes(pdf_bytes, tmpdir)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

import fitz  # PyMuPDF
from PIL import Image
import os
import io
import base64
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from tempfile import TemporaryDirectory

app = FastAPI()

class PDFBase64Request(BaseModel):
    pdf_base64: str

def extract_strips_from_pdf_bytes(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to open PDF: {str(e)}")

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

        # Sort by Y and remove false duplicates (too close)
        starts.sort(key=lambda x: x["y_start"])
        filtered_starts = []
        for s in starts:
            if not filtered_starts or abs(s["y_start"] - filtered_starts[-1]["y_start"]) > THRESHOLD:
                filtered_starts.append(s)

        if not filtered_starts:
            print(f"⚠️ No headers found on page {page_num + 1}")
            continue

        # Prepare cut points
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

            print(f"✅ Saved: {filename} from Y={int(y0)} to Y={int(y1)}")

    doc.close()
    return result

@app.post("/extract")
async def extract_from_base64_pdf(request: PDFBase64Request):
    try:
        pdf_bytes = base64.b64decode(request.pdf_base64)
        with TemporaryDirectory() as tmpdir:
            result = extract_strips_from_pdf_bytes(pdf_bytes, tmpdir)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
