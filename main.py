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
        raise HTTPException(status_code=500, detail=str(e))

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

    MIN_HEIGHT = 40
    MIN_DISTANCE = 5  # Reduced to detect closely spaced strips

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        starts = []

        for b in blocks:
            for l in b.get("lines", []):
                spans = l.get("spans", [])
                line_text = " ".join([s["text"] for s in spans]).strip()

                # Match header pattern
                match = re.search(r'\bL[O0A]\b\s+(\S+)', line_text.upper())
                if match:
                    y = l["bbox"][1]
                    dossier = match.group(1).strip()
                    starts.append({"y_start": y, "dossier": dossier})
                else:
                    # Fallback: check individual spans for "LO" or "LA"
                    for idx, s in enumerate(spans):
                        if s["text"].upper() in ["LO", "LA", "L0"]:
                            y = l["bbox"][1]
                            # Try getting next span as dossier
                            if idx + 1 < len(spans):
                                dossier = spans[idx + 1]["text"].strip()
                            else:
                                dossier = f"Unknown_Page{page_num+1}"
                            starts.append({"y_start": y, "dossier": dossier})
                            break

        # Sort by y and filter duplicates
        starts.sort(key=lambda x: x["y_start"])
        filtered_starts = []
        for s in starts:
            if not filtered_starts or abs(s["y_start"] - filtered_starts[-1]["y_start"]) > MIN_DISTANCE:
                filtered_starts.append(s)

        if not filtered_starts:
            print(f"⚠️ No headers found on page {page_num + 1}")
            continue

        cut_points = [s["y_start"] for s in filtered_starts]
        cut_points.append(page.rect.height)

        for i in range(len(filtered_starts)):
            y0 = cut_points[i]
            y1 = cut_points[i + 1]

            if y1 <= y0 or (y1 - y0) < MIN_HEIGHT:
                continue

            rect = fitz.Rect(0, y0, page.rect.width, y1)
            pix = page.get_pixmap(clip=rect, dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))

            row = str(i + 1)
            dossier = filtered_starts[i]["dossier"]
            filename = f"{dossier}_{page_num+1}_{row}.pdf"
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

import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
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

def preprocess_image(image):
    # Convert to grayscale and enhance contrast
    image = ImageOps.grayscale(image)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Increase contrast
    return image

def extract_dossier_headers(image):
    image = preprocess_image(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    headers = []

    for i, word in enumerate(data['text']):
        if word.upper() in ['LO', 'LA', 'L0'] and i + 1 < len(data['text']):
            dossier = data['text'][i + 1]
            y = data['top'][i]
            if re.match(r'^\d+$', dossier):  # Only numeric dossier numbers
                headers.append((y, dossier))
    
    return sorted(headers, key=lambda x: x[0])

def extract_strips_from_pdf_bytes(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        image = Image.open(io.BytesIO(pix.tobytes()))
        headers = extract_dossier_headers(image)

        if not headers:
            print(f"❌ No headers found on page {page_num+1}")
            continue

        headers.append((image.height, "END"))

        for i in range(len(headers) - 1):
            y0 = headers[i][0]
            y1 = headers[i + 1][0]
            dossier = headers[i][1]

            if y1 <= y0 or (y1 - y0) < 40:  # Minimum height check
                continue

            strip = image.crop((0, y0, image.width, y1))
            filename = f"{dossier}_{i+1}.pdf"
            output_path = os.path.join(output_dir, filename)

            strip.save(output_path, "PDF", resolution=300.0)

            with open(output_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            result.append({
                "filename": filename,
                "filedata": encoded
            })

            print(f"✅ Saved strip: {filename} Y={y0}-{y1}")

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

'''import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
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

def preprocess_image(image):
    image = ImageOps.grayscale(image)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(2.5)

def extract_dossier_headers(image, page_num):
    image = preprocess_image(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config='--psm 6')
    headers = []

    for i, word in enumerate(data['text']):
        word = word.strip().upper()
        if word in ['LO', 'LA', 'L0'] and i + 1 < len(data['text']):
            next_word = data['text'][i + 1].strip()
            if re.fullmatch(r'\d+', next_word):  # Accept only digits
                y = data['top'][i]
                headers.append((y, next_word))
            else:
                y = data['top'][i]
                headers.append((y, f"Unknown_{page_num}_{i}"))

    return sorted(headers, key=lambda x: x[0])

def extract_strips_from_pdf_bytes(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    MIN_HEIGHT = 40
    MIN_DISTANCE = 5

    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        image = Image.open(io.BytesIO(pix.tobytes()))
        headers = extract_dossier_headers(image, page_num)

        if not headers:
            print(f"❌ No headers found on page {page_num+1}")
            continue

        # Ensure last cut point includes end of page
        headers.append((image.height, "END"))

        i = 0
        while i < len(headers) - 1:
            y0 = headers[i][0]
            y1 = headers[i + 1][0]
            dossier = headers[i][1]

            if y1 <= y0 or (y1 - y0) < MIN_HEIGHT:
                i += 1
                continue

            rect = (0, y0, image.width, y1)
            cropped = image.crop(rect)

            filename = f"{dossier}_{page_num+1}_{i+1}.pdf"
            output_path = os.path.join(output_dir, filename)
            cropped.save(output_path, "PDF", resolution=300.0)

            with open(output_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            result.append({
                "filename": filename,
                "filedata": encoded
            })

            print(f"✅ Saved: {filename} | Y={y0}-{y1}")
            i += 1

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
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
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

def preprocess_image(image):
    image = ImageOps.grayscale(image)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(2.5)

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

            # Skip duplicate or near-duplicate Y positions
            if any(abs(y - sy) < 10 for sy in seen_y):
                continue
            seen_y.add(y)

            if re.fullmatch(r'\d+', next_word):
                headers.append((y, next_word))
            else:
                headers.append((y, f"Unknown_{page_num}_{i}"))

    # Sort by y-position
    return sorted(headers, key=lambda x: x[0])

def extract_strips_from_pdf_bytes(pdf_bytes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    result = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    MIN_HEIGHT = 50  # pixels

    for page_num, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        image = Image.open(io.BytesIO(pix.tobytes()))
        headers = extract_dossier_headers(image, page_num, image.height)

        if not headers:
            print(f"❌ No headers found on page {page_num+1}")
            continue

        # Don't blindly add image.height unless last strip is incomplete
        cut_points = headers.copy()
        last_y = cut_points[-1][0]
        if (image.height - last_y) >  (MIN_HEIGHT + 20) and "Unknown" not in cut_points[-1][1]:
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
                # If last entry is unknown, and all strips were extracted above, skip
                print(f"⛔ Skipped unknown strip at Y={y0} (height={y1 - y0})") 
                continue

            filename = f"{dossier}_{i+1}.pdf"
            output_path = os.path.join(output_dir, filename)
            cropped.save(output_path, "PDF", resolution=300.0)

            with open(output_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            result.append({
                "filename": filename,
                "filedata": encoded
            })

            print(f"✅ Saved: {filename} | Y={y0}-{y1}")

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
