# Generate Local Leads (Zero-Cost)

> Master directive for autonomous B2B lead generation.

## Goal
Given a business type and location, generate a list of verified leads with email addresses and push to Google Sheets.

## Inputs
- `query`: Business type + location (e.g., "Plumbers in Chicago")
- `limit`: Maximum number of leads to collect (default: 50)
- `sheet_name`: Name of the Google Sheet to create/update

## Outputs
- Google Sheet with columns: `Name | Website | Email | Phone | Address | Verified`
- Intermediate files in `.tmp/` for debugging

## Execution Flow

### Step 1: Discovery (Google Maps)
**Script:** `execution/scrape_google_maps.py`
**Input:** `query`, `limit`
**Output:** `.tmp/maps_results.json`

Scrape Google Maps for businesses matching the query. Extract:
- Business Name
- Address
- Phone Number
- Website URL
- Rating/Review Count

**Rate Limiting:** Add 5-15 second delays between actions to mimic human behavior.

### Step 2: Email Extraction (Website Crawl)
**Script:** `execution/crawl_website_for_email.py`
**Input:** `.tmp/maps_results.json`
**Output:** `.tmp/emails_found.json`

For each business with a website:
1. Visit homepage
2. Check `/contact`, `/about`, `/team` pages
3. Scan footer for `mailto:` links
4. Regex extract any email patterns

### Step 3: Email Verification (SMTP)
**Script:** `execution/verify_email_smtp.py`
**Input:** `.tmp/emails_found.json`
**Output:** `.tmp/verified_leads.json`

For each lead:
1. If email found, verify via SMTP handshake
2. If no email found, try common patterns (`info@`, `contact@`, `hello@`)
3. Mark as `verified`, `unverified`, or `catch-all`

### Step 4: Delivery (Google Sheets)
**Script:** `execution/push_to_sheets.py`
**Input:** `.tmp/verified_leads.json`, `sheet_name`
**Output:** Google Sheet URL

Push final lead list to Google Sheets with proper formatting.

## Edge Cases & Learnings

- **Google Maps blocks:** If blocked, wait 30 minutes before retrying. Consider using residential proxies in future.
- **Websites without emails:** Some businesses only have contact forms. Mark these as "no email" but include phone.
- **SMTP verification failures:** Some servers block SMTP checks. Fall back to "unverified" status.
- **Catch-all domains:** Some domains accept any email. Mark as "catch-all" so user knows deliverability is uncertain.

## Example Usage

```bash
python execution/run_lead_gen.py "HVAC companies in Texas" --limit 100 --sheet "Texas HVAC Leads"
```
