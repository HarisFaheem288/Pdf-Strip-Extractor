## 📄 PDF Strip Extractor

A FastAPI-powered service that extracts individual strip sections from a multi-strip scanned PDF document. Each strip typically starts with a "LO" or "LA" header and contains dossier information.

---

### 🚀 Features

* 📑 Accepts PDF input in base64 format via a FastAPI endpoint
* ✂️ Automatically detects and splits strips based on header patterns (`LO`, `LA`, or `L0`)
* 🖼 Converts each strip into a separate **PDF file**
* ⚙️ Clean output — each strip is saved separately
* 💻 Can be integrated into larger document processing pipelines

---

### 🧠 How It Works

1. The PDF is decoded from base64 and read using **PyMuPDF (`fitz`)**.
2. Each page is scanned for text patterns like `LO`, `LA`, or `L0` using **regex matching**.
3. The vertical (Y-axis) positions of these headers are used to determine cutting points.
4. Each section between headers is **clipped**, converted to image using **`get_pixmap()`**, and then saved as an individual PDF.
5. Output is base64-encoded again and returned as JSON.

---

### 📦 Tech Stack

* **Python**
* **FastAPI** – API framework
* **PyMuPDF (fitz)** – PDF reading & processing
* **Pillow (PIL)** – Image handling
* **Base64** – Encoding/decoding input/output

---

### 📥 API Usage

#### `POST /extract`

**Request Body:**

```json
{
  "pdf_base64": "your_base64_encoded_pdf_here"
}
```

**Response:**

```json
[
  {
    "filename": "12345-1.pdf",
    "filedata": "base64_pdf_content"
  },
  ...
]
```

---

### 📁 Output Structure

Each extracted strip is saved and returned with:

* **Filename**: `<dossier-number>-<row-number>.pdf`
* **Filedata**: Base64-encoded PDF content

---

### 🧪 Example Use Cases

* Dossier-based scanning & record-keeping
* Bulk document digitization
* Automated input for OCR/ML pipelines

---

### 🛠 Installation & Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

