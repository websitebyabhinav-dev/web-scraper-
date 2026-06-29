from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import json

app = FastAPI()

@app.get("/")
def home():
    return {"status": "alive"}

@app.post("/scrap")
async def scrap(request: Request):
    try:
        data = await request.json()
        url = data.get("url")

        if not url:
            return JSONResponse({"error": "URL missing"}, status_code=400)

        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)

        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.text.strip() if soup.title else "No Title"
        links = [a.get("href") for a in soup.find_all("a", href=True)][:50]

        output = {
            "url": url,
            "title": title,
            "links": links
        }

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("data.json", json.dumps(output, indent=4))

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=datavenator.zip"}
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)