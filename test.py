import base64
import requests

with open("sample.pdf", "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

res = requests.post("http://127.0.0.1:8000/extract", json={"pdf_base64": encoded})

if res.status_code != 200:
    print("Request failed:", res.text)
    exit()

data = res.json()

for file_obj in data:
    filename = file_obj["filename"]
    filedata = file_obj["filedata"]
    with open(filename, "wb") as f:
        f.write(base64.b64decode(filedata))
    print(f"✅ Saved: {filename}")
