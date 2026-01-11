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


# HARDCODED SHEET URL - RESET STRATEGY
SHEET_URL = "https://docs.google.com/spreadsheets/d/1b9DrDkl1eUKKtyFFxXd_xt-3IaVObV25tKsTE0bn2xY/edit?usp=sharing"

def create_or_open_sheet(client, sheet_name=None):
    """Open the Master Sheet by exact URL (ignores sheet_name arg)."""
    try:
        print(f"[*] Opening Master Sheet by URL...")
        sheet = client.open_by_url(SHEET_URL)
        print(f"[*] Successfully opened definition: {sheet.title}")
        return sheet
    except Exception as e:
        print(f"[!] CRITICAL ERROR opening sheet URL: {e}")
        print(f"[!] Verify bot-user@gen-lang-client-0510712247.iam.gserviceaccount.com has EDITOR access.")
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


def push_to_sheets(leads: list, sheet_name: str, industry: str = None, location: str = None) -> str:
    """
    Push leads to Google Sheets.
    
    Args:
        leads: List of lead dictionaries
        sheet_name: Name of the sheet to create/update
        
    Returns:
        URL of the created/updated sheet
    """
    print(f"[*] Pushing {len(leads)} leads to Google Sheets...")
    print(f"[*] Target Sheet: {sheet_name}")
    
    client = get_gspread_client()
    spreadsheet = create_or_open_sheet(client, sheet_name)
    
    # Get the first worksheet
    worksheet = spreadsheet.sheet1
    
    # Find next available row
    existing_values = worksheet.get_all_values()
    next_row = len(existing_values) + 1
    
    # 1. Add Separator / Title Row
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct descriptive title
    if industry and location:
        title_text = f"SEARCH: {industry} in {location} | {timestamp} | Found {len(leads)} leads"
    else:
        title_text = f"SEARCH: {timestamp} - Found {len(leads)} leads"
        
    title_row_content = [title_text] + [""] * 7
    
    worksheet.update(f'A{next_row}', [title_row_content])
    
    # Format Title Row (Green + Bold)
    worksheet.format(f'A{next_row}:H{next_row}', {
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}},
        'backgroundColor': {'red': 0.1, 'green': 0.5, 'blue': 0.1}, # Green
        'horizontalAlignment': 'LEFT'
    })
    
    next_row += 1

    # 2. Add Headers
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
    
    # Prepare data rows
    rows = [headers]
    for lead in leads:
        rows.append(format_lead_for_sheet(lead))
    
    # Batch update data
    worksheet.update(rows, f'A{next_row}')
    
    # Format Header Row (Dark Gray)
    worksheet.format(f'A{next_row}:H{next_row}', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })
    
    # Auto-resize columns (careful not to resize too often if sheet is huge)
    # worksheet.columns_auto_resize(0, 7)
    
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
    parser.add_argument("--industry", type=str, help="Industry name")
    parser.add_argument("--location", type=str, help="Location name")
    args = parser.parse_args()
    
    leads = load_leads(Path(args.input))
    sheet_url = push_to_sheets(leads, args.sheet, args.industry, args.location)
    
    print(f"\n[✓] Done! View your leads at:\n{sheet_url}")
    
    return sheet_url


if __name__ == "__main__":
    main()
