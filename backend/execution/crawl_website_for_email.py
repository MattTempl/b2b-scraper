#!/usr/bin/env python3
"""
Website Email Crawler

Crawls websites to extract email addresses from contact pages,
about pages, and footer sections.
"""

import json
import re
import time
import random
from pathlib import Path
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# Paths
TMP_DIR = Path(__file__).parent.parent / ".tmp"
INPUT_FILE = TMP_DIR / "maps_results.json"
OUTPUT_FILE = TMP_DIR / "emails_found.json"

# Email regex pattern
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# Common contact page paths to check
CONTACT_PATHS = [
    '/contact',
    '/contact-us',
    '/contactus',
    '/about',
    '/about-us',
    '/aboutus',
    '/team',
    '/our-team',
    '/staff',
    '/get-in-touch',
]

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Timeout for requests
REQUEST_TIMEOUT = 10


def extract_emails_from_html(html: str) -> set:
    """Extract all email addresses from HTML content."""
    # Decode common obfuscation patterns
    html = html.replace('[at]', '@').replace('[dot]', '.')
    html = html.replace(' at ', '@').replace(' dot ', '.')
    html = html.replace('(at)', '@').replace('(dot)', '.')
    
    emails = set(EMAIL_PATTERN.findall(html))
    
    # Filter out common false positives
    filtered = set()
    for email in emails:
        email_lower = email.lower()
        # Skip image files, example emails, etc
        if any(x in email_lower for x in ['.png', '.jpg', '.gif', '.svg', 'example.com', 'email.com', 'domain.com', 'yoursite', 'yourdomain']):
            continue
        # Skip WordPress/system emails
        if any(x in email_lower for x in ['wordpress', 'woocommerce', 'admin@localhost']):
            continue
        filtered.add(email)
    
    return filtered


def get_base_url(url: str) -> str:
    """Get base URL from full URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_website(website: str) -> str:
    """Ensure website has proper URL format."""
    if not website:
        return None
    
    website = website.strip()
    
    # Remove trailing slashes
    website = website.rstrip('/')
    
    # Add protocol if missing
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    return website


def fetch_page(url: str) -> str:
    """Fetch a page and return HTML content."""
    try:
        response = requests.get(
            url, 
            headers=HEADERS, 
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            verify=False  # Some sites have SSL issues
        )
        response.raise_for_status()
        return response.text
    except Exception:
        return ""


def crawl_website_for_emails(website: str) -> set:
    """
    Crawl a website to find email addresses.
    Checks homepage and common contact pages.
    """
    emails = set()
    website = normalize_website(website)
    
    if not website:
        return emails
    
    base_url = get_base_url(website)
    pages_to_check = [website] + [urljoin(base_url, path) for path in CONTACT_PATHS]
    
    for page_url in pages_to_check:
        try:
            html = fetch_page(page_url)
            if html:
                found = extract_emails_from_html(html)
                emails.update(found)
                
                # Also check mailto links specifically
                soup = BeautifulSoup(html, 'lxml')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('mailto:'):
                        email = href.replace('mailto:', '').split('?')[0].strip()
                        if EMAIL_PATTERN.match(email):
                            emails.add(email)
            
            # Small delay between requests to same domain
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception:
            continue
    
    return emails


def process_lead(lead: dict) -> dict:
    """Process a single lead to find emails."""
    website = lead.get('website')
    
    if website:
        emails = crawl_website_for_emails(website)
        lead['emails_found'] = list(emails)
        lead['primary_email'] = list(emails)[0] if emails else None
        print(f"  [✓] {lead.get('name', 'Unknown')}: Found {len(emails)} email(s)")
    else:
        lead['emails_found'] = []
        lead['primary_email'] = None
        print(f"  [–] {lead.get('name', 'Unknown')}: No website")
    
    return lead


def crawl_all_websites(leads: list, max_workers: int = 5) -> list:
    """
    Crawl all websites in parallel to find emails.
    """
    print(f"[*] Crawling {len(leads)} websites for emails...")
    
    results = []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_lead, lead): lead for lead in leads}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                lead = futures[future]
                lead['emails_found'] = []
                lead['primary_email'] = None
                lead['error'] = str(e)
                results.append(lead)
    
    # Count stats
    with_email = sum(1 for r in results if r.get('primary_email'))
    print(f"[*] Found emails for {with_email}/{len(results)} leads ({(100*with_email//len(results)) if results else 0}%)")
    
    return results


def load_leads(input_file: Path = INPUT_FILE) -> list:
    """Load leads from JSON file."""
    with open(input_file, 'r') as f:
        return json.load(f)


def save_results(leads: list, output_file: Path = OUTPUT_FILE):
    """Save results to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(leads, f, indent=2)
    print(f"[*] Saved results to {output_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Crawl websites for email addresses")
    parser.add_argument("--input", type=str, default=str(INPUT_FILE), help="Input JSON file")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON file")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers")
    args = parser.parse_args()
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    leads = load_leads(Path(args.input))
    results = crawl_all_websites(leads, max_workers=args.workers)
    save_results(results, Path(args.output))
    
    return results


if __name__ == "__main__":
    main()
