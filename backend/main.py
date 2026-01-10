from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import json
import asyncio

app = FastAPI()

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
        
        # We define a sheet name based on the query to keep things organized
        sheet_name = f"Leads: {query}"
        
        # Prepare environment
        env = os.environ.copy()
        
        # Command: python3 execution/run_lead_gen.py "Query" --limit 50 --sheet "Name"
        # Flags: --skip-crawl --skip-verify (for speed/safety on MVP)
        cmd = [
            "python3", "execution/run_lead_gen.py",
            query,
            "--limit", str(request.limit),
            "--sheet", sheet_name,
            "--skip-crawl", # Default to speed for web demo
            "--skip-verify"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd="backend", # Run from backend dir
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
        
        process = subprocess.Popen(
            ["python3", "execution/find_venues.py"],
            cwd="backend", # Run from backend dir so paths align
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
