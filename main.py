from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import mimetypes

from zip import ZipBuilder

app = FastAPI()

ALLOWED_ORIGIN = "https://datavenator.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVELOPER_PROFILE = {
    "developer": {
        "name": "Abhinav",
        "alias": "Lulzex",
        "role": "Lead Architect & Digital Visionary",
        "biography": "Behind every line of code, every architectural marvel, and every seamless deployment stands Abhinav, known globally in the digital underground and tech spheres as Lulzex. Operating as a standalone architect, he doesn't just build applications—he constructs digital ecosystems. From high-level infrastructure design to flawless execution, the entire empire is engineered by a single mind.",
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
        "call_to_action": "Don't just watch the empire grow—be a part of it. Click the link and subscribe now."
    }
}

def check_origin(request: Request):
    origin = request.headers.get("origin")
    if origin != ALLOWED_ORIGIN:
        raise HTTPException(status_code=403, detail="Blocked origin")

def safe_filename(url: str, default_ext: str = "") -> str:
    """Extracts a safe filename from a URL query path."""
    path = urlparse(url).path
    filename = path.split("/")[-1]
    if not filename:
        return f"asset_{hash(url) & 0xffffffff}{default_ext}"
    if "." not in filename and default_ext:
        filename += default_ext
    return filename

@app.get("/")
def home():
    return {"status": "alive"}

@app.post("/scrap")
async def scrap(request: Request):
    try:
        check_origin(request)

        data = await request.json()
        url = data.get("url")

        if not url:
            return JSONResponse({"error": "URL missing"}, status_code=400)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # 1. Fetch main target landing markup
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200:
            return JSONResponse({"error": f"Failed fetching target site: HTTP {res.status_code}"}, status_code=400)
            
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.title.text.strip() if soup.title else "No Title"

        # Initialize core structure zip engine
        zip_builder = ZipBuilder()
        
        # Track counts for metadata output
        css_count = 0
        js_count = 0
        img_count = 0

        # 2. Extract & Clone Cascading Style Sheet assets (CSS)
        for link_tag in soup.find_all("link", rel="stylesheet"):
            href = link_tag.get("href")
            if href:
                absolute_css_url = urljoin(url, href)
                try:
                    css_res = requests.get(absolute_css_url, headers=headers, timeout=5)
                    if css_res.status_code == 200:
                        file_name = safe_filename(absolute_css_url, ".css")
                        # Write into a dedicated subfolder layout inside the zip
                        zip_builder.add_text(f"css/{file_name}", css_res.text)
                        # Re-route the source link inside HTML to read locally
                        link_tag["href"] = f"css/{file_name}"
                        css_count += 1
                except Exception:
                    pass  # Skip unreachable or timed out assets gracefully

        # 3. Extract & Clone JavaScript asset payloads (JS)
        for script_tag in soup.find_all("script", src=True):
            src = script_tag.get("src")
            if src:
                absolute_js_url = urljoin(url, src)
                try:
                    js_res = requests.get(absolute_js_url, headers=headers, timeout=5)
                    if js_res.status_code == 200:
                        file_name = safe_filename(absolute_js_url, ".js")
                        zip_builder.add_text(f"js/{file_name}", js_res.text)
                        script_tag["src"] = f"js/{file_name}"
                        js_count += 1
                except Exception:
                    pass

        # 4. Extract, Download and map Image binary arrays
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")
            if src:
                absolute_img_url = urljoin(url, src)
                try:
                    img_res = requests.get(absolute_img_url, headers=headers, timeout=5)
                    if img_res.status_code == 200:
                        file_name = safe_filename(absolute_img_url)
                        # Add as a binary stream instead of plain text string
                        zip_builder.add_bytes(f"images/{file_name}", img_res.content)
                        img_tag["src"] = f"images/{file_name}"
                        img_count += 1
                except Exception:
                    pass

        # Collect raw links summary for historical telemetry records 
        all_hyperlinks = [urljoin(url, a.get("href")) for a in soup.find_all("a", href=True)]

        telemetry_output = {
            "url": url,
            "title": title,
            "cloned_metrics": {
                "css_files": css_count,
                "javascript_files": js_count,
                "images_saved": img_count
            },
            "total_extracted_links": len(all_hyperlinks),
            "links_sample": all_hyperlinks[:150],
        }

        # 5. Pack everything tightly into deployment zip structure
        # Use updated modified local resource soup text
        zip_builder.add_text("index.html", str(soup)) 
        zip_builder.add_json("metrics.json", telemetry_output)
        zip_builder.add_json("developer.profile.json", DEVELOPER_PROFILE)
        zip_builder.add_text("manifest_links_log.txt", "\n".join(all_hyperlinks))

        zip_buffer = zip_builder.close()

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=datavenator_clone.zip"
            }
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
