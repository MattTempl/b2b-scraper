#!/usr/bin/env python3
"""
Google Maps Scraper - Apify API Version

Uses Apify's Google Places Crawler for fast, reliable scraping.
Much faster than local Playwright - runs in Apify's cloud.
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Ensure .tmp directory exists
TMP_DIR = Path(__file__).parent.parent / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = TMP_DIR / "maps_results.json"

# Apify actor for Google Maps
# Using the popular "compass/crawler-google-places" actor
APIFY_ACTOR_ID = "compass/crawler-google-places"


def get_apify_client():
    """Get authenticated Apify client."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise ValueError(
            "APIFY_API_TOKEN not found in environment.\n"
            "Please add it to .env file:\n"
            "APIFY_API_TOKEN=your_token_here\n\n"
            "Get your token from: https://console.apify.com/settings/integrations"
        )
    return ApifyClient(token)


def scrape_google_maps(query: str, limit: int = 50) -> list:
    """
    Scrape Google Maps using Apify's cloud scraper.
    
    Args:
        query: Search query (e.g., "Plumbers in Chicago")
        limit: Maximum number of results to collect
        
    Returns:
        List of business dictionaries
    """
    print(f"[*] Starting Apify Google Maps scraper...")
    print(f"[*] Query: {query}")
    print(f"[*] Limit: {limit}")
    
    client = get_apify_client()
    
    # Prepare input for the actor
    run_input = {
        "searchStringsArray": [query],
        "maxCrawledPlacesPerSearch": limit,
        "language": "en",
        "includeWebResults": False,
        "maxImages": 0,
        "maxReviews": 0,
        "scrapeContacts": True,  # Extract emails from websites
        "scrapeDirectories": False,
    }
    
    print(f"[*] Running Apify actor: {APIFY_ACTOR_ID}")
    
    # Run the actor and wait for it to finish
    run = client.actor(APIFY_ACTOR_ID).call(run_input=run_input)
    
    print(f"[*] Actor finished with status: {run.get('status')}")
    
    # Fetch results from the dataset
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    print(f"[*] Retrieved {len(dataset_items)} results from Apify")
    
    # Transform to our standard format
    results = []
    for item in dataset_items:
        business = {
            "name": item.get("title", ""),
            "address": item.get("address", ""),
            "phone": item.get("phone", ""),
            "website": item.get("website", ""),
            "rating": item.get("totalScore", ""),
            "review_count": item.get("reviewsCount", 0),
        }
        
        # Apify returns emails as an array
        emails = item.get("emails", [])
        if emails:
            business["email"] = emails[0]  # Use first email
            business["all_emails"] = emails  # Store all emails found
        
        if business.get("name"):
            results.append(business)
            print(f"  [{len(results)}/{len(dataset_items)}] {business['name']}")
    
    return results


def save_results(results: list, output_file: Path = OUTPUT_FILE):
    """Save results to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[*] Saved {len(results)} results to {output_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Google Maps using Apify")
    parser.add_argument("query", help="Search query (e.g., 'Plumbers in Chicago')")
    parser.add_argument("--limit", type=int, default=50, help="Max results to collect")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON file")
    args = parser.parse_args()
    
    results = scrape_google_maps(args.query, args.limit)
    save_results(results, Path(args.output))
    
    return results


if __name__ == "__main__":
    main()
