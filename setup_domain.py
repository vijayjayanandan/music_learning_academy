"""
Domain Setup Script — onemusicapp.com
Automates: Cloudflare DNS + Render custom domains + Django prod settings verification.

Usage:
    python setup_domain.py

Requires .env with:
    CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID, RENDER_API_KEY, RENDER_SERVICE_ID
"""

import os
import sys
import requests
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# Config
DOMAIN = "onemusicapp.com"
RENDER_TARGET = "music-academy-dk9c.onrender.com"

CF_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
CF_ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID", "")
RENDER_API_KEY = os.environ.get("RENDER_API_KEY", "")
RENDER_SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "")

CF_HEADERS = {
    "Authorization": f"Bearer {CF_TOKEN}",
    "Content-Type": "application/json",
}
RENDER_HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json",
}

CF_BASE = "https://api.cloudflare.com/client/v4"
RENDER_BASE = "https://api.render.com/v1"


def check_env():
    """Verify all required env vars are set."""
    missing = []
    if not CF_TOKEN:
        missing.append("CLOUDFLARE_API_TOKEN")
    if not CF_ZONE_ID:
        missing.append("CLOUDFLARE_ZONE_ID")
    if not RENDER_API_KEY:
        missing.append("RENDER_API_KEY")
    if not RENDER_SERVICE_ID:
        missing.append("RENDER_SERVICE_ID")
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        print("Fill them in .env and retry.")
        sys.exit(1)
    print("[OK] All env vars present")


def verify_cloudflare_token():
    """Verify the Cloudflare API token works."""
    r = requests.get(f"{CF_BASE}/user/tokens/verify", headers=CF_HEADERS)
    data = r.json()
    if not data.get("success"):
        print(f"ERROR: Cloudflare token verification failed: {data.get('errors')}")
        sys.exit(1)
    print(f"[OK] Cloudflare token valid (status: {data['result']['status']})")


def get_existing_dns_records():
    """Fetch existing DNS records for the zone."""
    r = requests.get(
        f"{CF_BASE}/zones/{CF_ZONE_ID}/dns_records",
        headers=CF_HEADERS,
        params={"per_page": 100},
    )
    data = r.json()
    if not data.get("success"):
        print(f"ERROR: Failed to fetch DNS records: {data.get('errors')}")
        sys.exit(1)
    return data["result"]


def create_or_update_dns(record_type, name, content, proxied=False):
    """Create or update a DNS record."""
    existing = get_existing_dns_records()

    # Check if record already exists
    for rec in existing:
        if rec["type"] == record_type and rec["name"] == name:
            if rec["content"] == content and rec["proxied"] == proxied:
                print(f"[SKIP] DNS {record_type} {name} -> {content} (already exists)")
                return rec
            # Update existing record
            r = requests.put(
                f"{CF_BASE}/zones/{CF_ZONE_ID}/dns_records/{rec['id']}",
                headers=CF_HEADERS,
                json={
                    "type": record_type,
                    "name": name,
                    "content": content,
                    "proxied": proxied,
                    "ttl": 1,  # Auto
                },
            )
            data = r.json()
            if data.get("success"):
                print(f"[UPDATED] DNS {record_type} {name} -> {content} (proxied={proxied})")
                return data["result"]
            else:
                print(f"ERROR: Failed to update DNS: {data.get('errors')}")
                sys.exit(1)

    # Create new record
    r = requests.post(
        f"{CF_BASE}/zones/{CF_ZONE_ID}/dns_records",
        headers=CF_HEADERS,
        json={
            "type": record_type,
            "name": name,
            "content": content,
            "proxied": proxied,
            "ttl": 1,  # Auto
        },
    )
    data = r.json()
    if data.get("success"):
        print(f"[CREATED] DNS {record_type} {name} -> {content} (proxied={proxied})")
        return data["result"]
    else:
        print(f"ERROR: Failed to create DNS: {data.get('errors')}")
        sys.exit(1)


def setup_cloudflare_dns():
    """Create CNAME records pointing to Render."""
    print("\n--- Cloudflare DNS Setup ---")

    # Root domain: CNAME flattening (Cloudflare auto-flattens CNAME at apex)
    create_or_update_dns("CNAME", DOMAIN, RENDER_TARGET, proxied=False)

    # www subdomain
    create_or_update_dns("CNAME", f"www.{DOMAIN}", RENDER_TARGET, proxied=False)

    print("[OK] Cloudflare DNS configured")


def get_render_custom_domains():
    """Fetch existing custom domains for the Render service."""
    r = requests.get(
        f"{RENDER_BASE}/services/{RENDER_SERVICE_ID}/custom-domains",
        headers=RENDER_HEADERS,
    )
    if r.status_code != 200:
        print(f"ERROR: Failed to fetch Render domains: {r.status_code} {r.text}")
        sys.exit(1)
    return r.json()


def add_render_custom_domain(domain_name):
    """Add a custom domain to the Render service."""
    existing = get_render_custom_domains()

    # Check if already exists (response is a list of {cursor, customDomain} objects)
    for item in existing:
        d = item.get("customDomain", {}) if isinstance(item, dict) else {}
        if d.get("name") == domain_name:
            status = d.get("verificationStatus", "unknown")
            print(f"[SKIP] Render domain {domain_name} (already exists, status={status})")
            return d

    r = requests.post(
        f"{RENDER_BASE}/services/{RENDER_SERVICE_ID}/custom-domains",
        headers=RENDER_HEADERS,
        json={"name": domain_name},
    )
    if r.status_code in (200, 201):
        data = r.json()
        d = data.get("customDomain", data) if isinstance(data, dict) else data
        print(f"[CREATED] Render domain {domain_name}")
        return d
    elif r.status_code == 409:
        print(f"[SKIP] Render domain {domain_name} (already exists on this service)")
        return None
    else:
        print(f"ERROR: Failed to add Render domain {domain_name}: {r.status_code} {r.text}")
        sys.exit(1)


def setup_render_domains():
    """Add custom domains to Render service."""
    print("\n--- Render Custom Domains ---")

    add_render_custom_domain(DOMAIN)
    add_render_custom_domain(f"www.{DOMAIN}")

    print("[OK] Render custom domains configured")
    print("     Render will auto-provision SSL certificates (may take a few minutes)")


def verify_django_settings():
    """Check that prod.py has the custom domain in ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS."""
    print("\n--- Django Settings Check ---")

    prod_path = Path(__file__).parent / "config" / "settings" / "prod.py"
    content = prod_path.read_text()

    issues = []
    if DOMAIN not in content:
        issues.append(f"ALLOWED_HOSTS missing {DOMAIN}")
    if f"https://{DOMAIN}" not in content:
        issues.append(f"CSRF_TRUSTED_ORIGINS missing https://{DOMAIN}")

    if issues:
        print(f"[WARN] Django prod.py needs updates: {', '.join(issues)}")
        print("       Run this script with --fix-django or update manually")
    else:
        print("[OK] Django prod.py already has custom domain config")


def main():
    print(f"=== Domain Setup: {DOMAIN} ===")
    print(f"    Target: {RENDER_TARGET}\n")

    check_env()
    verify_cloudflare_token()
    setup_cloudflare_dns()
    setup_render_domains()
    verify_django_settings()

    print("\n=== Setup Complete ===")
    print(f"  DNS:    {DOMAIN} -> {RENDER_TARGET}")
    print(f"  DNS:    www.{DOMAIN} -> {RENDER_TARGET}")
    print(f"  Render: Custom domains added, SSL auto-provisioning")
    print(f"\nNext steps:")
    print(f"  1. Wait 1-5 min for DNS propagation")
    print(f"  2. Check Render dashboard for SSL cert status")
    print(f"  3. Visit https://{DOMAIN} to verify")


if __name__ == "__main__":
    main()
