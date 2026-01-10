#!/usr/bin/env python3
"""
SMTP Email Verifier

Verifies email addresses using SMTP handshake and DNS MX lookup.
Also generates common email patterns for businesses without found emails.
"""

import json
import socket
import smtplib
import dns.resolver
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# Paths
TMP_DIR = Path(__file__).parent.parent / ".tmp"
INPUT_FILE = TMP_DIR / "emails_found.json"  
OUTPUT_FILE = TMP_DIR / "verified_leads.json"

# Common email patterns to try (in order of likelihood)
EMAIL_PATTERNS = [
    'info@{domain}',
    'contact@{domain}',
    'hello@{domain}',
    'sales@{domain}',
    'support@{domain}',
    'admin@{domain}',
    'office@{domain}',
    '{first}@{domain}',
    '{first}.{last}@{domain}',
    '{first}{last}@{domain}',
]

# Timeout for SMTP operations
SMTP_TIMEOUT = 10


def get_domain_from_website(website: str) -> str:
    """Extract domain from website URL."""
    if not website:
        return None
    
    try:
        parsed = urlparse(website)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.lower()
    except:
        return None


def get_mx_records(domain: str) -> list:
    """Get MX records for a domain."""
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange).rstrip('.') for r in records]
    except:
        return []


def verify_email_smtp(email: str, mx_host: str = None) -> dict:
    """
    Verify email using SMTP handshake.
    
    Returns:
        dict with 'valid', 'catch_all', and 'error' keys
    """
    result = {
        'email': email,
        'valid': False,
        'catch_all': False,
        'error': None
    }
    
    domain = email.split('@')[1]
    
    # Get MX records if not provided
    if not mx_host:
        mx_records = get_mx_records(domain)
        if not mx_records:
            result['error'] = 'No MX records'
            return result
        mx_host = mx_records[0]
    
    try:
        # Connect to mail server
        with smtplib.SMTP(timeout=SMTP_TIMEOUT) as smtp:
            smtp.connect(mx_host, 25)
            smtp.helo('check.local')
            smtp.mail('verify@check.local')
            code, _ = smtp.rcpt(email)
            
            if code == 250:
                result['valid'] = True
            elif code == 550:
                result['valid'] = False
            else:
                # Some codes like 252 mean "can't verify but might exist"
                result['valid'] = None  # Unknown
                
    except smtplib.SMTPServerDisconnected:
        result['error'] = 'Server disconnected'
    except smtplib.SMTPConnectError:
        result['error'] = 'Connection failed'
    except socket.timeout:
        result['error'] = 'Timeout'
    except Exception as e:
        result['error'] = str(e)
    
    return result


def check_catch_all(domain: str) -> bool:
    """Check if domain has catch-all enabled."""
    fake_email = f"definitely_fake_12345@{domain}"
    result = verify_email_smtp(fake_email)
    return result.get('valid', False)


def generate_email_guesses(lead: dict) -> list:
    """Generate possible email addresses for a lead."""
    website = lead.get('website')
    domain = get_domain_from_website(website)
    
    if not domain:
        return []
    
    # Try to extract first/last name from business name
    name = lead.get('name', '')
    name_parts = name.split()
    first = name_parts[0].lower() if name_parts else ''
    last = name_parts[-1].lower() if len(name_parts) > 1 else ''
    
    guesses = []
    for pattern in EMAIL_PATTERNS:
        email = pattern.format(
            domain=domain,
            first=first,
            last=last
        )
        # Only add if pattern was fully resolved
        if '{' not in email and '@' in email:
            guesses.append(email)
    
    return guesses


def process_lead(lead: dict) -> dict:
    """Process a single lead - verify existing or guess new emails."""
    name = lead.get('name', 'Unknown')
    
    # If we already found an email, verify it
    if lead.get('primary_email'):
        email = lead['primary_email']
        result = verify_email_smtp(email)
        
        if result['valid']:
            lead['verified_email'] = email
            lead['email_status'] = 'verified'
            print(f"  [✓] {name}: {email} (verified)")
        elif result['valid'] is None:
            lead['verified_email'] = email
            lead['email_status'] = 'unverified'
            print(f"  [?] {name}: {email} (unverified)")
        else:
            lead['verified_email'] = None
            lead['email_status'] = 'invalid'
            print(f"  [✗] {name}: {email} (invalid)")
        
        return lead
    
    # No email found - try to guess
    website = lead.get('website')
    domain = get_domain_from_website(website)
    
    if not domain:
        lead['verified_email'] = None
        lead['email_status'] = 'no_website'
        print(f"  [–] {name}: No website")
        return lead
    
    # Check for catch-all first
    is_catch_all = check_catch_all(domain)
    
    if is_catch_all:
        # If catch-all, use info@ as best guess
        lead['verified_email'] = f"info@{domain}"
        lead['email_status'] = 'catch_all'
        print(f"  [~] {name}: info@{domain} (catch-all)")
        return lead
    
    # Try common patterns
    guesses = generate_email_guesses(lead)
    
    for guess in guesses[:5]:  # Limit to first 5 guesses
        result = verify_email_smtp(guess)
        if result['valid']:
            lead['verified_email'] = guess
            lead['email_status'] = 'guessed_verified'
            print(f"  [✓] {name}: {guess} (guessed & verified)")
            return lead
    
    # No valid email found
    lead['verified_email'] = f"info@{domain}"  # Best guess
    lead['email_status'] = 'guessed_unverified'
    print(f"  [?] {name}: info@{domain} (guessed, unverified)")
    
    return lead


def verify_all_leads(leads: list, max_workers: int = 3) -> list:
    """
    Verify or guess emails for all leads.
    Uses limited parallelism to avoid rate limiting.
    """
    print(f"[*] Verifying emails for {len(leads)} leads...")
    
    results = []
    
    # Lower parallelism for SMTP to avoid blocks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_lead, lead): lead for lead in leads}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                lead = futures[future]
                lead['verified_email'] = None
                lead['email_status'] = 'error'
                lead['verification_error'] = str(e)
                results.append(lead)
    
    # Stats
    verified = sum(1 for r in results if r.get('email_status') in ['verified', 'guessed_verified'])
    catch_all = sum(1 for r in results if r.get('email_status') == 'catch_all')
    unverified = sum(1 for r in results if 'unverified' in r.get('email_status', ''))
    no_email = sum(1 for r in results if r.get('email_status') in ['no_website', 'invalid', 'error'])
    
    print(f"\n[*] Results:")
    print(f"    Verified: {verified}")
    print(f"    Catch-all: {catch_all}")
    print(f"    Unverified: {unverified}")
    print(f"    No email: {no_email}")
    
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
    parser = argparse.ArgumentParser(description="Verify email addresses via SMTP")
    parser.add_argument("--input", type=str, default=str(INPUT_FILE), help="Input JSON file")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON file")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel workers")
    args = parser.parse_args()
    
    leads = load_leads(Path(args.input))
    results = verify_all_leads(leads, max_workers=args.workers)
    save_results(results, Path(args.output))
    
    return results


if __name__ == "__main__":
    main()
