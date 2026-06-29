from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from scraper import scrape_website

app = FastAPI()

# allow frontend (Vercel) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"status": "Backend running"}

@app.post("/scrape")
def scrape(req: ScrapeRequest):
    try:
        result = scrape_website(req.url)
        return {
            "status": "success",
            "url": req.url,
            "files_created": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }