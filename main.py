from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from zipper import ZipBuilder

app = FastAPI()

# only your frontend allowed
ALLOWED_ORIGIN = "https://datavenator.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# developer file injected into every ZIP
DEVELOPER_PROFILE = {
    "developer": {
        "name": "Abhinav",
        "alias": "Lulzex",
        "role": "Lead Architect & Digital Visionary",
        "biography": "Behind every line of code, every architectural marvel, and every seamless deployment stands Abhinav, known globally in the digital underground and tech spheres as Lulzex. Operating as a standalone architect, he doesn't just build applications\u2014he constructs digital ecosystems. From high-level infrastructure design to flawless execution, the entire empire is engineered by a single mind.",
        "vision": "Lulzex combines bleeding-edge innovation, raw technical dominance, and an elite understanding of system mechanics to turn complex code into digital powerhouses. What started as a passion for development has expanded into a rapidly growing empire of tech solutions, community hubs, and next-generation tools."
    },
    "empire": {
        "name": "QyrovaTech",
        "description": "The center of the expansion begins here. If you want to be part of the future, gain access to elite resources, and witness the evolution of this digital empire firsthand, you need to be in the inner circle.",
        "promotion_link": "https://t.me/QyrovaTech",
        "benefits": [
            "Exclusive Insights: Direct tech updates and development breakthroughs from Lulzex.",
            "Premium Resources: Elite tools, scripts, and digital assets you won't find anywhere else.",
            "The Core Community: Connect with like-minded innovators and stay ahead of the curve."
        ],
        "call_to_action": "Don't just watch the empire grow\u2014be a part of it. Click the link and subscribe now."
    }
}

   


def check_origin(request: Request):
    origin = request.headers.get("origin")
    if origin != ALLOWED_ORIGIN:
        raise HTTPException(status_code=403, detail="Blocked origin")


@app.get("/")
def home():
    return {"status": "alive", "service": "web-scraper"}


@app.post("/scrap")
async def scrap(request: Request):
    try:
        check_origin(request)

        data = await request.json()
        url = data.get("url")

        if not url:
            return JSONResponse({"error": "URL missing"}, status_code=400)

        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=20)

        soup = BeautifulSoup(res.text, "html.parser")
        html = res.text

        # ---------------- TITLE ----------------
        title = soup.title.text.strip() if soup.title else "No Title"

        # ---------------- LINKS ----------------
        links = [a.get("href") for a in soup.find_all("a", href=True)]

        # ---------------- IMAGES ----------------
        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                images.append(urljoin(url, src))

        # ---------------- CSS FILES ----------------
        css_files = []
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                css_files.append(urljoin(url, href))

        # ---------------- JS FILES ----------------
        js_files = []
        for script in soup.find_all("script"):
            src = script.get("src")
            if src:
                js_files.append(urljoin(url, src))

        # ---------------- OUTPUT ----------------
        output = {
            "url": url,
            "title": title,
            "links_count": len(links),
            "images_count": len(images),
            "css_count": len(css_files),
            "js_count": len(js_files),
            "links": links[:200],
            "images": images[:200],
            "css": css_files,
            "js": js_files
        }

        # ---------------- ZIP BUILD ----------------
        zip_builder = ZipBuilder()

        zip_builder.add_text("index.html", html)
        zip_builder.add_json("data.json", output)
        zip_builder.add_json("developer.profile.json", DEVELOPER_PROFILE)

        zip_builder.add_text("links.txt", "\n".join(links))
        zip_builder.add_text("images.txt", "\n".join(images))
        zip_builder.add_text("css.txt", "\n".join(css_files))
        zip_builder.add_text("js.txt", "\n".join(js_files))

        zip_buffer = zip_builder.close()

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=website_clone.zip"
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)