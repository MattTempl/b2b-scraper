from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import json
import asyncio
import uuid

# Store background jobs: job_id -> process
JOBS = {}

from pathlib import Path

# Force deploy v2 - 2026-01-10T17:31

app = FastAPI()

# Temp directory for jobs
current_dir = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = Path(current_dir).parent / ".tmp"
JOBS_DIR = TMP_DIR / "jobs"

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
    Uses a master sheet that the user must create and share.
    """
    try:
        query = f"{request.industry} in {request.location}"
        
        # Master sheet - user must create this and share with Service Account
        sheet_name = "B2B Scraper Results"
        
        # Prepare environment
        env = os.environ.copy()
        
        # Calculate absolute path to the script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "execution", "run_lead_gen.py")
        
        if not os.path.exists(script_path):
             raise FileNotFoundError(f"Script not found at: {script_path}")

        # Command
        cmd = [
            "python3", script_path,
            query,
            "--limit", str(request.limit),
            "--sheet", sheet_name,
            "--industry", request.industry,
            "--location", request.location,
            "--skip-crawl",
            "--skip-verify",
        ]
        
        # Generate Job ID
        job_id = str(uuid.uuid4())
        cmd.extend(["--job-id", job_id])
        
        # Fire and forget - start the process and return immediately
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
            env=env
        )
        
        # We don't need to store process object anymore for status, 
        # but good to keep reference if we want to kill it later.
        JOBS[job_id] = process

        return {
            "status": "Job Started",
            "job_id": job_id,
            "message": f"Scraping '{query}'. Results will appear in your 'B2B Scraper Results' sheet when finished.",
            "sheet_name": sheet_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of a background job from file system."""
    status_file = JOBS_DIR / f"{job_id}.json"
    
    if not status_file.exists():
        # Fallback to checking memory if file not created yet (very early)
        if job_id in JOBS:
             if JOBS[job_id].poll() is None:
                 return {"status": "running"}
        return {"status": "running"} # Assume running if just started
    
    try:
        with open(status_file, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"status": "failed", "error": f"Failed to read status: {str(e)}"}

@app.get("/api/debug-sheet")
async def debug_sheet():
    """Debug endpoint to check Google Sheets access on Render."""
    try:
        import gspread
        import json
        
        # 1. Check Env Var
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            return {"status": "Error", "message": "GOOGLE_CREDENTIALS env var is MISSING"}
            
        # 2. Parse JSON
        try:
            creds_dict = json.loads(creds_json)
            client_email = creds_dict.get('client_email', 'UNKNOWN')
        except json.JSONDecodeError:
             return {"status": "Error", "message": "GOOGLE_CREDENTIALS is not valid JSON"}

        # 3. Authenticate
        try:
            gc = gspread.service_account_from_dict(creds_dict)
            client = gc
        except Exception as e:
            return {"status": "Error", "message": f"Auth failed: {str(e)}"}

        # 4. Try Master Sheet
        try:
            sheet = client.open("B2B Scraper Results")
            return {
                "status": "Success", 
                "message": "Connected to sheet!",
                "sheet_title": sheet.title,
                "sheet_url": sheet.url,
                "authenticated_as": client_email
            }
        except gspread.SpreadsheetNotFound:
            return {
                "status": "Error", 
                "message": f"Sheet 'B2B Scraper Results' NOT FOUND for user {client_email}. Did you share it?",
                "authenticated_as": client_email
            }
        except Exception as e:
            return {"status": "Error", "message": f"Open failed: {str(e)}", "authenticated_as": client_email}

    except Exception as e:
        return {"status": "Critical Error", "message": str(e)}

@app.get("/api/test-sheet-write")
async def test_sheet_write_endpoint():
    """Trigger a dummy data write to verify permissions."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "test_sheet_render.py")
        
        cmd = ["python3", script_path]
        result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}

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
