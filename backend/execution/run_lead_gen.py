#!/usr/bin/env python3
"""
Lead Generation Orchestrator

Master script that runs the full lead generation pipeline:
1. Scrape Google Maps
2. Crawl websites for emails
3. Verify emails via SMTP
4. Push results to Google Sheets

Usage:
    python run_lead_gen.py "Plumbers in Chicago" --limit 50 --sheet "Chicago Plumbers"
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json
import time

# Script paths
EXECUTION_DIR = Path(__file__).parent
SCRAPE_MAPS = EXECUTION_DIR / "scrape_google_maps.py"
CRAWL_EMAILS = EXECUTION_DIR / "crawl_website_for_email.py"
VERIFY_EMAILS = EXECUTION_DIR / "verify_email_smtp.py"
PUSH_SHEETS = EXECUTION_DIR / "push_to_sheets.py"

# Temp file paths
# Robust path resolution: resolve() ensures we get absolute path free of symlinks/..
TMP_DIR = Path(__file__).resolve().parent.parent.parent / ".tmp"
JOBS_DIR = TMP_DIR / "jobs"

def update_status(job_id: str, status: str, msg: str = None, error: str = None):
    """Write job status to a JSON file."""
    if not job_id:
        return
        
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    status_file = JOBS_DIR / f"{job_id}.json"
    
    data = {
        "job_id": job_id,
        "status": status,
        "message": msg,
        "error": error,
        "updated_at": datetime.now().isoformat()
    }
    
    with open(status_file, 'w') as f:
        json.dump(data, f)



def run_step(name: str, cmd: list) -> bool:
    """Run a pipeline step and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {name} failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run the full lead generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_lead_gen.py "HVAC companies in Texas" --limit 100 --sheet "Texas HVAC Leads"
    python run_lead_gen.py "Restaurants in Miami" --limit 50 --sheet "Miami Restaurants"
        """
    )
    parser.add_argument(
        "query", 
        help="Search query (e.g., 'Plumbers in Chicago')"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=50, 
        help="Maximum number of leads to collect (default: 50)"
    )
    parser.add_argument(
        "--sheet", 
        type=str, 
        help="Name of the Google Sheet (default: auto-generated from query)"
    )
    parser.add_argument(
        "--skip-maps",
        action="store_true",
        help="Skip Google Maps scraping (use existing data)"
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        default=True,
        help="Skip website crawling (default: True for speed)"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        default=True,
        help="Skip email verification (default: True for speed)"
    )
    parser.add_argument(
        "--skip-sheets",
        action="store_true",
        help="Skip pushing to Google Sheets"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        help="Unique Job ID for status tracking"
    )
    parser.add_argument("--industry", type=str, help="Industry name")
    parser.add_argument("--location", type=str, help="Location name")
    
    args = parser.parse_args()
    
    # Generate sheet name if not provided
    sheet_name = args.sheet or f"{args.query} - {datetime.now().strftime('%Y-%m-%d')}"
    
     print(f"""
╔══════════════════════════════════════════════════════════════╗
║           B2B LEAD GENERATION PIPELINE                       ║
╠══════════════════════════════════════════════════════════════╣
║  Query: {args.query:<52} ║
║  Limit: {str(args.limit):<52} ║
║  Sheet: {sheet_name:<52} ║
║  Ind  : {str(args.industry):<52} ║
║  Loc  : {str(args.location):<52} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print(f"[*] Raw Args: {args}") # Debug logging
    
    # Ensure tmp directory exists
    TMP_DIR.mkdir(exist_ok=True)
    
    # Init Status
    update_status(args.job_id, "running", f"Starting pipeline for '{args.query}'")

    # Step 1: Scrape Google Maps
    if not args.skip_maps:
        success = run_step(
            "Google Maps Scraping",
            [sys.executable, str(SCRAPE_MAPS), args.query, "--limit", str(args.limit)]
        )
        if not success:
            print("\n[!] Pipeline stopped at Google Maps scraping")
            update_status(args.job_id, "failed", error="Google Maps scraping failed")
            sys.exit(1)
    else:
        print("\n[*] Skipping Google Maps scraping...")
    
    # Step 2: Crawl websites for emails
    if not args.skip_crawl:
        success = run_step(
            "Website Email Crawling",
            [sys.executable, str(CRAWL_EMAILS)]
        )
        if not success:
            print("\n[!] Pipeline stopped at website crawling")
            update_status(args.job_id, "failed", error="Website crawling failed")
            sys.exit(1)
    else:
        print("\n[*] Skipping website crawling...")
    
    # Step 3: Verify emails
    if not args.skip_verify:
        success = run_step(
            "Email Verification (SMTP)",
            [sys.executable, str(VERIFY_EMAILS)]
        )
        if not success:
            print("\n[!] Pipeline stopped at email verification")
            update_status(args.job_id, "failed", error="Email verification failed")
            sys.exit(1)
    else:
        print("\n[*] Skipping email verification...")
    
    # Step 4: Push to Google Sheets
    # Use maps_results.json directly if we skipped crawling/verification
    input_file = str(TMP_DIR / "maps_results.json")
    if not args.skip_crawl and not args.skip_verify:
        input_file = str(TMP_DIR / "verified_leads.json")
    elif not args.skip_crawl:
        input_file = str(TMP_DIR / "emails_found.json")
    
    if not args.skip_sheets:
        print(f"[*] Pushing to Sheets using file: {input_file}")
        with open(input_file, 'r') as f:
            print(f"[*] File size: {len(f.read())} bytes")
            
        success = run_step(
            "Google Sheets Export",
            [
                sys.executable, str(PUSH_SHEETS), 
                "--input", input_file, 
                "--sheet", sheet_name,
                "--industry", args.industry or "",
                "--location", args.location or ""
            ]
        )
        if not success:
            print("\n[!] Pipeline stopped at Google Sheets export")
            print("[*] Results are still saved in .tmp/verified_leads.json")
            update_status(args.job_id, "failed", error="Google Sheets export failed")
            sys.exit(1)
    else:
        print("\n[*] Skipping Google Sheets export...")
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    PIPELINE COMPLETE! ✓                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    update_status(args.job_id, "completed", "All steps finished successfully")


if __name__ == "__main__":
    main()
