#!/usr/bin/env python3
"""
Google Sheets Exporter

Pushes lead generation results to a Google Sheet.
Uses gspread with OAuth for free API access.
Supports both Service Account and User OAuth flows.
"""

import json
import os
from pathlib import Path
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Paths
TMP_DIR = Path(__file__).parent.parent / ".tmp"
INPUT_FILE = TMP_DIR / "verified_leads.json"
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_gspread_client():
    """Get authenticated gspread client using Service Account or OAuth."""
    # 1. Server-side: Check for Service Account (File or Env Var)
    
    # Check Local File (backend/service_account.json)
    # This script is in backend/execution, key is in backend/
    SERVICE_ACCOUNT_FILE = PROJECT_ROOT / "service_account.json"
    
    if SERVICE_ACCOUNT_FILE.exists():
        print(f"[*] Using Service Account Key: {SERVICE_ACCOUNT_FILE}")
        return gspread.service_account(filename=str(SERVICE_ACCOUNT_FILE))
        
    # Check Env Var (Render Deployment)
    if os.environ.get('GOOGLE_CREDENTIALS'):
        print("[*] Using Google Credentials from Environment")
        creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
        return gspread.service_account_from_dict(creds_dict)

    # 2. Local-side: Fallback to User OAuth
    creds = None
    
    # Check for existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # If no valid credentials, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                 # If we are here, we have neither Service Account nor User Creds
                 raise FileNotFoundError("Authentication Failed: No service_account.json or credentials.json found.")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), 
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"[*] Saved auth token to {TOKEN_FILE}")
    
    return gspread.authorize(creds)


def create_or_open_sheet(client, sheet_name: str):
    """Open an existing sheet (user must create and share it with the Service Account)."""
    try:
        sheet = client.open(sheet_name)
        print(f"[*] Opened existing sheet: {sheet_name}")
        return sheet
    except Exception as e:
        print(f"[!] Error opening sheet '{sheet_name}': {e}")
        print(f"[!] Make sure you created a sheet named '{sheet_name}' and shared it with the Service Account email.")
        raise


def format_lead_for_sheet(lead: dict) -> list:
    """Format a lead dictionary into a row for the spreadsheet."""
    # Get email from various possible field names
    email = (
        lead.get('email', '') or 
        lead.get('verified_email', '') or 
        lead.get('primary_email', '')
    )
    
    return [
        lead.get('name', ''),
        lead.get('website', ''),
        email,
        lead.get('phone', ''),
        lead.get('address', ''),
        lead.get('rating', ''),
        lead.get('review_count', ''),
        lead.get('email_status', ''),
    ]


def push_to_sheets(leads: list, sheet_name: str) -> str:
    """
    Push leads to Google Sheets.
    
    Args:
        leads: List of lead dictionaries
        sheet_name: Name of the sheet to create/update
        
    Returns:
        URL of the created/updated sheet
    """
    print(f"[*] Pushing {len(leads)} leads to Google Sheets...")
    
    client = get_gspread_client()
    spreadsheet = create_or_open_sheet(client, sheet_name)
    
    # Get the first worksheet
    worksheet = spreadsheet.sheet1
    
    # Clear existing data
    worksheet.clear()
    
    # Set up headers
    headers = [
        'Name',
        'Website', 
        'Email',
        'Phone',
        'Address',
        'Rating',
        'Reviews',
        'Email Status'
    ]
    
    # Prepare all data
    rows = [headers]
    for lead in leads:
        rows.append(format_lead_for_sheet(lead))
    
    # Batch update (much faster than individual updates)
    worksheet.update(rows, 'A1')
    
    # Format header row
    worksheet.format('A1:H1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'horizontalAlignment': 'CENTER'
    })
    
    # Freeze header row
    worksheet.freeze(rows=1)
    
    # Auto-resize columns
    worksheet.columns_auto_resize(0, 7)
    
    sheet_url = spreadsheet.url
    print(f"[*] Sheet URL: {sheet_url}")
    
    return sheet_url


def load_leads(input_file: Path = INPUT_FILE) -> list:
    """Load leads from JSON file."""
    with open(input_file, 'r') as f:
        return json.load(f)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Push leads to Google Sheets")
    parser.add_argument("--input", type=str, default=str(INPUT_FILE), help="Input JSON file")
    parser.add_argument("--sheet", type=str, required=True, help="Name of the Google Sheet")
    args = parser.parse_args()
    
    leads = load_leads(Path(args.input))
    sheet_url = push_to_sheets(leads, args.sheet)
    
    print(f"\n[✓] Done! View your leads at:\n{sheet_url}")
    
    return sheet_url


if __name__ == "__main__":
    main()
