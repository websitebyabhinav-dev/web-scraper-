from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import io
import zipfile

app = FastAPI()

# FIX: allow frontend to call backend (VERY IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "server running"}

@app.post("/scrap")
async def scrap(request: Request):
    data = await request.json()
    url = data.get("url")

    if not url:
        return {"error": "No URL provided"}

    try:
        # STEP 1: fetch website
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return {"error": f"Failed to fetch site: {res.status_code}"}

        # STEP 2: parse HTML
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else "No Title"
        links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

        # STEP 3: create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("title.txt", title)
            zip_file.writestr("links.txt", "\n".join(str(x) for x in links[:50]))
            zip_file.writestr("source.html", res.text)

        zip_buffer.seek(0)

        # STEP 4: return ZIP
        return Response(
            content=zip_buffer.read(),
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=datavenator.zip"
            }
        )

    except Exception as e:
        return {"error": str(e)}