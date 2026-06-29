from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import json
from urllib.parse import urljoin

app = FastAPI()

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        res = requests.get(url, headers=headers, timeout=20)

        soup = BeautifulSoup(res.text, "html.parser")

        # TITLE
        title = soup.title.text.strip() if soup.title else "No Title"

        # LINKS (absolute)
        links = []
        for a in soup.find_all("a", href=True):
            links.append(urljoin(url, a["href"]))
        links = links[:100]

        # IMAGES (absolute)
        images = []
        for img in soup.find_all("img", src=True):
            images.append(urljoin(url, img["src"]))
        images = images[:100]

        # META TAGS
        meta = {}
        for m in soup.find_all("meta"):
            name = m.get("name") or m.get("property")
            content = m.get("content")
            if name and content:
                meta[name] = content

        # FULL HTML SNAPSHOT
        html_snapshot = res.text

        output = {
            "url": url,
            "title": title,
            "links": links,
            "images": images,
            "meta": meta
        }

        # ZIP BUILD
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("data.json", json.dumps(output, indent=4))
            z.writestr("page.html", html_snapshot)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=scraped_site.zip"
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)