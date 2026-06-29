from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import json
from urllib.parse import urljoin

app = FastAPI()

# Allow only your site (basic protection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://datavenator.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin != "https://datavenator.vercel.app":
        raise HTTPException(status_code=403, detail="Blocked origin")


@app.get("/")
def home():
    return {"status": "alive", "mode": "advanced scraper"}


@app.post("/scrap")
async def scrap(request: Request):
    try:
        check_origin(request)

        data = await request.json()
        url = data.get("url")

        if not url:
            return JSONResponse({"error": "URL missing"}, status_code=400)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        res = requests.get(url, headers=headers, timeout=20)
        html = res.text

        soup = BeautifulSoup(html, "html.parser")

        # -----------------------------
        # 1. FULL HTML
        # -----------------------------
        full_html = html

        # -----------------------------
        # 2. TITLE
        # -----------------------------
        title = soup.title.text.strip() if soup.title else "No Title"

        # -----------------------------
        # 3. LINKS
        # -----------------------------
        links = [a.get("href") for a in soup.find_all("a", href=True)]

        # -----------------------------
        # 4. IMAGES
        # -----------------------------
        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                images.append(urljoin(url, src))

        # -----------------------------
        # 5. CSS FILES
        # -----------------------------
        css_files = []
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                css_files.append(urljoin(url, href))

        # -----------------------------
        # 6. JS FILES
        # -----------------------------
        js_files = []
        for script in soup.find_all("script"):
            src = script.get("src")
            if src:
                js_files.append(urljoin(url, src))

        # -----------------------------
        # FINAL STRUCTURE
        # -----------------------------
        output = {
            "url": url,
            "title": title,
            "links": links[:100],
            "images": images[:100],
            "css": css_files,
            "js": js_files,
            "html_size": len(html)
        }

        # -----------------------------
        # CREATE ZIP
        # -----------------------------
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:

            z.writestr("page.html", full_html)
            z.writestr("data.json", json.dumps(output, indent=4))

            # Save images list (NOT downloading files, only links)
            z.writestr("images.txt", "\n".join(images))

            z.writestr("links.txt", "\n".join(links))

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=dev_scrape_package.zip"
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)