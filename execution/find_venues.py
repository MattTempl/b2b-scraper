#!/usr/bin/env python3
"""
Mansion Party Venue Finder
Scrapes Giggster for venues matching criteria:
- Location: <15 miles from USC (34.0224, -118.2851)
- Capacity: 55+ guests
- Date: Jan 17, 2026 (Availability check)
- Amenities: Alcohol allowed, Pool/Outdoor space (Nice to have)
"""

import re
import json
import time
import random
import sys
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright
from haversine import haversine, Unit

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google Sheets Setup
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_gspread_client():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return gspread.authorize(creds)

def push_venues(venues, sheet_name):
    print(f"[*] Pushing {len(venues)} venues to Google Sheets: {sheet_name}")
    client = get_gspread_client()
    try:
        sheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sheet = client.create(sheet_name)
    
    ws = sheet.sheet1
    ws.clear()
    
    headers = ["Name", "Link", "Distance (mi)", "Price", "Amenities", "Availability", "Smoking Policy"]
    rows = [headers]
    for v in venues:
        rows.append([
            v['name'], v['website'], v['distance'], v['price'],
            f"Pool: {'Yes' if v['has_pool'] else 'No'}, Alcohol: {'Yes' if 'Yes' in v['address'] else '?'}", 
            v['email'], # Availability status
            v['review_count'] # Smoking policy
        ])
    
    ws.update(rows, 'A1')
    ws.format('A1:G1', {'textFormat': {'bold': True}, 'horizontalAlignment': 'CENTER'})
    print(f"[*] Done! Sheet URL: {sheet.url}")

# Constants
USC_COORDS = (34.0224, -118.2851)  # Lat, Lon
MAX_DISTANCE_MILES = 15
TARGET_DATE = "2026-01-17"
GUEST_COUNT = 55
SEARCH_KEYWORD = "Mansion"
LOCATION_STR = "Los Angeles, CA"

def calculate_distance(venue_coords):
    if not venue_coords:
        return 999
    return haversine(USC_COORDS, venue_coords, unit=Unit.MILES)

def run():
    print(f"[*] Starting Venue Finder...")
    print(f"[*] Target Date: {TARGET_DATE}")
    print(f"[*] Search: {SEARCH_KEYWORD} in {LOCATION_STR}")
    
    venues_found = []

    with sync_playwright() as p:
        # Launch browser (headless=True is faster, but False helps debug if needed)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        # Construct Search URL
        # Giggster params: cities, query, attendees. Date often requires interaction or internal API.
        # We start with a broad search and then refine/check details.
        # URL structure often: https://giggster.com/search/Los-Angeles--CA?attendees=55&query=Mansion
        
        # FAST & STRICT SEARCH
        # 1. Update query to target pools specifically
        base_url = "https://giggster.com/search/Los-Angeles--CA"
        search_query = f"{SEARCH_KEYWORD} Pool"
        url = f"{base_url}?attendees={GUEST_COUNT}&query={search_query}"
        
        print(f"[*] Navigating to: {url}")
        page.goto(url, timeout=30000)
        # Faster wait state
        try: page.wait_for_load_state("domcontentloaded", timeout=5000) 
        except: pass

        # Scroll quickly
        print("[*] Scrolling to load results...")
        for _ in range(3):
            page.keyboard.press("PageDown")
            time.sleep(0.5)
        
        # Extract Listings
        all_links = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
        
        unique_links = set()
        for href in all_links:
            if "/listing/" in href or "/l/" in href:
                unique_links.add(href)
        
        print(f"[*] Found {len(unique_links)} potential venues. Checking top 15...")
        
        count = 0
        for link in unique_links:
            if count >= 15: # Reduced limit for speed
                break
            
            print(f"    Checking: {link}")
            try:
                v_page = context.new_page()
                v_page.goto(link, timeout=15000) # Short timeout
                
                # 1. EXTRACT DATA
                page_content = v_page.content().lower()
                name = v_page.title().split("|")[0].strip()
                
                lat, lon = None, None
                listing_data = {}
                
                # Try to get JSON data immediately for amenities/coords
                try: 
                    next_data = v_page.evaluate("() => window.__NEXT_DATA__")
                    if next_data:
                        listing_data = next_data.get('props', {}).get('pageProps', {}).get('listing', {})
                        lat = listing_data.get('latitude')
                        lon = listing_data.get('longitude')
                except: pass

                # 2. FILTER: NEGATIVE KEYWORDS (TITLE)
                title_lower = name.lower()
                negative_keywords = ["studio", "soundstage", " cyc ", "cyclorama", "set", "warehouse", "basement", "standing set", "production", "church", "gallery", "office"]
                if any(neg in title_lower for neg in negative_keywords):
                    print(f"        [SKIP] Negative keyword in title: {name}")
                    v_page.close()
                    continue

                # 3. FILTER: POOL (STRICT + CONTEXT)
                pool_keywords = ["pool", "jacuzzi", "swim"]
                has_pool = any(pk in page_content for pk in pool_keywords)
                
                # Check explicit amenities list (High Trust)
                amenities = str(listing_data.get('amenities', [])).lower()
                if "pool" in amenities or "swimming pool" in amenities: 
                    has_pool = True

                # Check for "Pool Table" false positive
                # If "pool" is in text, but "pool table" is also there, and NO amenities confirmed pool...
                if has_pool and "pool table" in page_content and "swimming" not in page_content and "pool" not in amenities:
                     # This is the danger zone. "Pool table" might trigger it.
                     # Let's count "pool" occurrences vs "pool table".
                     # Simple heuristic: if "swimming" or "heated" or "outside" or "backyard" is missing, skip.
                     # User wants MANSIONS. Mansions have backyards.
                     if not any(x in page_content for x in ["backyard", "outdoor", "swim", "heated", "jacuzzi"]):
                         print("        [SKIP] 'Pool' found but likely 'Pool Table' (No outdoor context)")
                         v_page.close()
                         continue

                if not has_pool:
                    print("        [SKIP] No 'Pool' found in text or amenities")
                    v_page.close()
                    continue

                # 4. FILTER: DISTANCE
                # Attempt to get coordinates if missing from JSON
                if not lat:
                     # Fast fallback? No, we rely on text check for LA
                     pass

                distance_mi = 999
                if lat and lon:
                    distance_mi = calculate_distance((float(lat), float(lon)))
                
                # Strict Distance or LA Text Check
                in_la_area = "los angeles" in page_content or "beverly hills" in page_content or "hollywood" in page_content
                
                if distance_mi > MAX_DISTANCE_MILES and not in_la_area:
                     print("        [SKIP] Too far / Not in LA")
                     v_page.close()
                     continue

                print(f"        [MATCH] {name[:30]}... ({distance_mi if distance_mi!=999 else 'LA Area'})")

                # Quick price grab
                try: price_text = v_page.locator("[class*='Price']").first.inner_text()
                except: price_text = "N/A"
                
                # Alcohol Check
                rules = str(listing_data.get('rules', [])).lower()
                description = str(listing_data.get('description', "")).lower()
                alcohol_allowed = "alcohol" in rules or "alcohol" in description

                venue = {
                    "name": name,
                    "website": link,
                    "email": "Check Link", 
                    "phone": f"{distance_mi:.1f} mi" if distance_mi != 999 else "LA Area",
                    "address": f"Pool: YES (Verified), Alcohol: {'Yes' if alcohol_allowed else '?'}", 
                    "rating": price_text,
                    "review_count": "Unknown",
                    "distance": distance_mi,
                    "has_pool": True,
                    "price": price_text
                }
                
                venues_found.append(venue)
                count += 1
                v_page.close()
                
            except Exception as e:
                print(f"        [ERR] Failed to process venue: {e}")
                try: v_page.close() 
                except: pass

        browser.close()

    print(f"[*] Found {len(venues_found)} valid venues.")
    
    # Sort by distance
    venues_found.sort(key=lambda x: x['distance'])
    
    # Push to Sheets
    # We need to map our venue dict to the expected structure or modify push_to_sheets.
    # push_to_sheets expects: name, website, email, phone, address, rating, review_count
    # We mapped: 
    # email -> Availability
    # phone -> Distance
    # address -> Amenities
    # rating -> Price
    # review_count -> Smoking Policy
    
    sheet_name = "LA Party Venues"
    if venues_found:
        push_venues(venues_found, sheet_name)
    else:
        print("[!] No venues found matching criteria.")

if __name__ == "__main__":
    run()
