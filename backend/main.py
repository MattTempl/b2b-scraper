from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import json
import asyncio

# Force deploy v2 - 2026-01-10T17:31

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class VenueSearchRequest(BaseModel):
    location: str
    radius: int
    pool_only: bool = True

class LeadGenRequest(BaseModel):
    industry: str
    location: str
    limit: int = 50

@app.get("/")
def read_root():
    return {"status": "Online", "service": "B2B Scraper API"}

@app.post("/api/run-lead-gen")
async def run_lead_gen(request: LeadGenRequest):
    """
    Triggers the General Lead Gen pipeline (Google Maps Scraper).
    """
    try:
        query = f"{request.industry} in {request.location}"
        
        # USE A MASTER SHEET
        # Creating new sheets with a Service Account makes them hidden/private.
        # Instead, we overwrite a single shared sheet so the user can actually see it.
        sheet_name = "B2B Scraper Results"
        
        # Prepare environment
        env = os.environ.copy()
        
        # Calculate absolute path to the script to avoid CWD issues
        # backend/main.py -> backend/execution/run_lead_gen.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "execution", "run_lead_gen.py")
        
        # Check if file exists (debug)
        if not os.path.exists(script_path):
             raise FileNotFoundError(f"Script not found at: {script_path}")

        # Command: python3 /abs/path/to/execution/run_lead_gen.py ...
        cmd = [
            "python3", script_path,
            query,
            "--limit", str(request.limit),
            "--sheet", sheet_name,
            "--skip-crawl", # Default to speed for web demo
            "--skip-verify"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        return {
            "status": "Job Started", 
            "pid": process.pid, 
            "message": f"Scraping '{query}'. Results will appear in sheet: {sheet_name}",
            "sheet_name": sheet_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-venue-finder")
async def run_venue_finder(request: VenueSearchRequest):
    """
    Triggers the find_venues.py script.
    Note: Ideally we refactor find_venues.py to be importable. 
    For now, we run it as a subprocess for isolation.
    """
    try:
        # We need to pass these args to the script via env vars or args.
        # For simplicity in this MVP, we assume the script is configured to look at Env Vars
        # OR we modify the script to take args.
        # Let's run the script and capture output.
        
        # NOTE: This blocks the worker. In a real production app, use Celery/Redis.
        # For a free tier tool for a friend, this is acceptable.
        
        env = os.environ.copy()
        # You would update find_venues.py to read these if dynamic
        # env['SEARCH_LOCATION'] = request.location
        
        # Absolute path fix for this endpoint too
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "execution", "find_venues.py")

        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # We return the PID so the frontend can poll (advanced) or just say "Started"
        return {"status": "Job Started", "pid": process.pid, "message": "Check Google Sheets in 2-3 minutes."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
