import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

from downloader import download_file
from zipper import create_zip

OUTPUT_DIR = "output/site"

def scrape_website(url):
    if os.path.exists(OUTPUT_DIR):
        import shutil
        shutil.rmtree(OUTPUT_DIR)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    # save HTML
    html_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    assets = []

    # CSS
    for link in soup.find_all("link"):
        href = link.get("href")
        if href:
            full_url = urljoin(url, href)
            assets.append(download_file(full_url, OUTPUT_DIR))

    # JS
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            full_url = urljoin(url, src)
            assets.append(download_file(full_url, OUTPUT_DIR))

    # Images
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            full_url = urljoin(url, src)
            assets.append(download_file(full_url, OUTPUT_DIR))

    zip_path = create_zip(OUTPUT_DIR)

    return {
        "html_saved": True,
        "assets_downloaded": len(assets),
        "zip_file": zip_path
    }