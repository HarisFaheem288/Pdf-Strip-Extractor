# 📄 PDF Strip Extractor with Dossier Number Detection

This project is a FastAPI-based web service that extracts **individual strips** (sections) from a base64-encoded PDF. Each strip is identified using OCR with **Tesseract** and saved as a separate PDF file with its associated **dossier number**.

> ✅ 100% accurate for PDFs where each strip contains a clear dossier header.
> ❌ Strips with unreadable headers are automatically ignored to prevent incorrect or partial extraction.

---

## 🚀 Features

* 🔍 **OCR-based strip detection** using Tesseract
* ✂️ Splits a multi-strip PDF into separate strip-PDFs
* 🧠 Detects headers like `LO 123456`, `LA 7890`, `L0 1111`
* 🗂️ Automatically names files as `DossierNumber_X.pdf`
* ❌ Skips unknown/partial or low-confidence headers
* ⚡ Powered by **FastAPI**

---

## 🧪 Example

### Input:

* PDF with multiple dossier sections labeled like `LO 123456`, `LA 654321`, etc.

### Output:

* A list of base64-encoded PDF files:

  * `123456_1.pdf`
  * `654321_2.pdf`
  * ...

Each containing one strip.

---

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/pdf-strip-extractor.git
   cd pdf-strip-extractor
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**

   * **Windows**: [Download here](https://github.com/tesseract-ocr/tesseract)
   * **Linux**:

     ```bash
     sudo apt update
     sudo apt install tesseract-ocr
     ```

4. *(Optional)* If on Windows, set the Tesseract path:

   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

---

## 🔥 Run the App

```bash
uvicorn main:app --reload
```

It will start the API on: `http://localhost:8000`

---

## 📬 API Usage

**Endpoint**: `POST /extract`

**Request JSON:**

```json
{
  "pdf_base64": "BASE64_ENCODED_PDF"
}
```

**Response JSON:**

```json
[
  {
    "filename": "123456_1.pdf",
    "filedata": "base64_encoded_file_data"
  },
  ...
]
```

---

## 🧠 How It Works

* Uses `PyMuPDF` to convert each page to an image
* Applies image preprocessing (grayscale + contrast enhancement)
* Uses `pytesseract` to detect headers like `LO <number>`
* Crops strips between header positions
* Saves each strip as a separate PDF file
* Returns the PDF strips in base64 format

---

## 📂 Example Dossier Header Pattern

Recognized headers must look like:

```
LO 123456
LA 7890
L0 112233
```

---

## 🛠️ Dependencies

```
fastapi
uvicorn
pytesseract
PyMuPDF
Pillow
