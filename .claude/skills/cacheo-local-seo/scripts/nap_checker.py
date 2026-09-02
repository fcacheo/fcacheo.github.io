#!/usr/bin/env python3
"""
nap_checker.py - NAP consistency checker for Cacheo Insurance Agency.

Compares the canonical NAP (assets/cacheo-nap.json) against listing data you
collect from each directory, and reports mismatches ordered by fix priority.

This tool does not browse. You collect the listing values (browser, or by
reading the directory page) into a listings JSON, then run this to diff them.
That keeps the comparison deterministic and auditable.

Usage:
    python3 nap_checker.py --listings listings.json
    python3 nap_checker.py --listings listings.json --output json
    python3 nap_checker.py --sample            # writes a listings skeleton to stdout

Exit codes:
    0  no mismatches
    1  mismatches found, none critical
    2  at least one Tier 1 (critical) mismatch
    3  bad input

Adapted from local-seo-manager/nap_checker.py in alirezarezvani/claude-skills (MIT).
Changes: insurance-specific directory tiers, canonical file default, state-suffix
normalization fix, hours comparison, exit codes, --sample skeleton.
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Tuple

CANONICAL_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "cacheo-nap.json",
)

# Tier 1 is where a wrong value costs money the same week. For a Farmers agent
# the corporate agent locator sits in Tier 1 alongside the map providers: it is
# the record several aggregators syndicate FROM, so an error there re-infects
# directories you already fixed by hand.
DIRECTORY_TIERS = {
    "google_business_profile": 1,
    "farmers_agent_locator": 1,
    "apple_maps": 1,
    "bing_places": 1,
    "yelp": 2,
    "bbb": 2,
    "facebook": 2,
    "nextdoor": 2,
    "yellow_pages": 3,
    "insurance_com": 3,
    "superpages": 3,
    "manta": 3,
    "chamber_of_commerce": 3,
}
TIER_LABELS = {1: "Critical", 2: "High", 3: "Medium"}

US_STATES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}

STREET_ABBREV = {
    r"\bst\b": "street",
    r"\bave\b": "avenue",
    r"\bblvd\b": "boulevard",
    r"\bhwy\b": "highway",
    r"\bdr\b": "drive",
    r"\brd\b": "road",
    r"\bln\b": "lane",
    r"\bct\b": "court",
    r"\bpl\b": "place",
    r"\bpkwy\b": "parkway",
    r"\bsuite\b": "ste",
    r"\bunit\b": "ste",
    r"\bn\b": "north",
    r"\bs\b": "south",
    r"\be\b": "east",
    r"\bw\b": "west",
}


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def normalize_name(name: str) -> str:
    name = (name or "").lower()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    for suffix in ("llc", "inc", "corp", "ltd", "co"):
        name = re.sub(rf"\b{suffix}\b", "", name).strip()
    return re.sub(r"\s+", " ", name).strip()


def normalize_state(value: str) -> str:
    """Normalize a value that is known to be a state field.

    Only called on the state sub-field. The upstream version expanded state
    abbreviations across the whole address string, which corrupts real Southern
    California street names -- 'La Palma Ave' became 'louisiana Palma Ave' via
    the \\bla\\b rule, and 'Ocean Blvd S' hit \\bs\\b. Scoping the expansion to
    the state field removes that whole class of false mismatch.
    """
    v = re.sub(r"[^\w\s]", " ", (value or "").lower()).strip()
    aliases = {"california": "ca", "calif": "ca"}
    v = aliases.get(v, v)
    return v if v in US_STATES else v


def normalize_address(address: str) -> str:
    a = (address or "").lower()
    for pattern, replacement in STREET_ABBREV.items():
        a = re.sub(pattern, replacement, a)
    a = re.sub(r"[^\w\s]", " ", a)
    return re.sub(r"\s+", " ", a).strip()


def normalize_hours(value: str) -> str:
    v = (value or "").lower().strip()
    v = v.replace("am", "").replace("pm", "")
    return re.sub(r"[\s:.-]+", "", v)


def compare_nap(canonical: Dict, listing: Dict) -> List[Dict]:
    """Return the list of field-level mismatches for one listing."""
    out: List[Dict] = []

    def flag(field, canon, found):
        out.append({"field": field, "canonical": canon, "found": found})

    if normalize_name(canonical.get("name")) != normalize_name(listing.get("name")):
        flag("name", canonical.get("name", ""), listing.get("name") or "(missing)")

    canon_phone = normalize_phone(canonical.get("phone"))
    found_phone = normalize_phone(listing.get("phone"))
    if canon_phone and not found_phone:
        flag("phone", canonical.get("phone", ""), "(missing)")
    elif canon_phone and canon_phone != found_phone:
        flag("phone", canonical.get("phone", ""), listing.get("phone", ""))

    canon_addr = canonical.get("address") or {}
    found_addr = listing.get("address") or {}
    if isinstance(canon_addr, dict) and isinstance(found_addr, dict):
        for sub in ("street", "city", "state", "zip"):
            norm = normalize_state if sub == "state" else normalize_address
            cv = norm(str(canon_addr.get(sub, "")))
            lv = norm(str(found_addr.get(sub, "")))
            if cv and not lv:
                flag(f"address.{sub}", canon_addr.get(sub, ""), "(missing)")
            elif cv and cv != lv:
                flag(f"address.{sub}", canon_addr.get(sub, ""), found_addr.get(sub, ""))
    elif canon_addr and found_addr:
        if normalize_address(str(canon_addr)) != normalize_address(str(found_addr)):
            flag("address", canon_addr, found_addr)

    canon_hours = canonical.get("hours") or {}
    found_hours = listing.get("hours") or {}
    if isinstance(found_hours, dict) and found_hours:
        for day, canon_val in canon_hours.items():
            if day not in found_hours:
                continue
            if normalize_hours(str(canon_val)) != normalize_hours(str(found_hours[day])):
                flag(f"hours.{day}", canon_val, found_hours[day])

    return out


def build_report(canonical: Dict, listings: List[Dict]) -> Tuple[str, Dict]:
    lines: List[str] = []
    summary = {
        "total_directories": len(listings),
        "consistent": 0,
        "with_mismatches": 0,
        "not_listed": 0,
        "critical_issues": 0,
        "issues": [],
    }

    addr = canonical.get("address", {})
    lines.append("=" * 68)
    lines.append("NAP CONSISTENCY REPORT - Cacheo Insurance Agency")
    lines.append("=" * 68)
    lines.append("")
    lines.append("CANONICAL")
    lines.append(f"  Name   : {canonical.get('name', 'N/A')}")
    if isinstance(addr, dict):
        lines.append(
            f"  Address: {addr.get('street','')}, {addr.get('city','')}, "
            f"{addr.get('state','')} {addr.get('zip','')}"
        )
    lines.append(f"  Phone  : {canonical.get('phone', 'N/A')}")
    lines.append(f"  Website: {canonical.get('website', 'N/A')}")

    unverified = (canonical.get("_unverified") or {}).get("fields") or []
    if unverified:
        lines.append("")
        lines.append(
            "  ! UNVERIFIED canonical fields: " + ", ".join(unverified)
        )
        lines.append(
            "    Confirm these against CLAUDE.md or the live listing before "
            "acting on any row that depends on them."
        )
    lines.append("")

    by_tier: Dict[int, List[str]] = {1: [], 2: [], 3: []}

    for listing in listings:
        directory = listing.get("directory", "unknown")
        tier = DIRECTORY_TIERS.get(directory, 3)
        label = directory.replace("_", " ").title()

        if not listing.get("listed", True):
            summary["not_listed"] += 1
            entry = f"[{TIER_LABELS[tier]}] {label}: NOT LISTED - claim this listing"
            by_tier[tier].append(entry)
            summary["issues"].append(
                {"directory": directory, "tier": tier, "type": "not_listed"}
            )
            if tier == 1:
                summary["critical_issues"] += 1
            continue

        mismatches = compare_nap(canonical, listing)
        if not mismatches:
            summary["consistent"] += 1
            continue

        summary["with_mismatches"] += 1
        if tier == 1:
            summary["critical_issues"] += 1
        for m in mismatches:
            by_tier[tier].append(
                f"[{TIER_LABELS[tier]}] {label} - {m['field']}: "
                f"expected '{m['canonical']}', found '{m['found']}'"
            )
            summary["issues"].append(
                {"directory": directory, "tier": tier, "type": "mismatch", **m}
            )

    lines.append("FIX ORDER")
    any_issue = False
    for tier in (1, 2, 3):
        if not by_tier[tier]:
            continue
        any_issue = True
        lines.append("")
        lines.append(f"-- Tier {tier} ({TIER_LABELS[tier]}) --")
        for entry in by_tier[tier]:
            lines.append(f"  {entry}")
    if not any_issue:
        lines.append("  No mismatches. Every listing checked matches canonical.")

    lines.append("")
    lines.append("-" * 68)
    lines.append(
        f"{summary['consistent']} consistent | "
        f"{summary['with_mismatches']} with mismatches | "
        f"{summary['not_listed']} not listed | "
        f"{summary['critical_issues']} critical"
    )
    return "\n".join(lines), summary


SAMPLE_LISTINGS = [
    {
        "directory": "google_business_profile",
        "url": "",
        "listed": True,
        "name": "",
        "phone": "",
        "address": {"street": "", "city": "", "state": "", "zip": ""},
        "hours": {},
    },
    {
        "directory": "farmers_agent_locator",
        "url": "",
        "listed": True,
        "name": "",
        "phone": "",
        "address": {"street": "", "city": "", "state": "", "zip": ""},
    },
    {"directory": "yelp", "url": "", "listed": True, "name": "", "phone": "",
     "address": {"street": "", "city": "", "state": "", "zip": ""}},
    {"directory": "bbb", "url": "", "listed": False},
]


def main() -> int:
    ap = argparse.ArgumentParser(description="NAP consistency checker (Cacheo)")
    ap.add_argument("--canonical", default=CANONICAL_DEFAULT,
                    help="canonical NAP JSON (default: assets/cacheo-nap.json)")
    ap.add_argument("--listings", help="collected listing data JSON")
    ap.add_argument("--output", choices=["text", "json"], default="text")
    ap.add_argument("--sample", action="store_true",
                    help="print a listings skeleton to fill in, then exit")
    args = ap.parse_args()

    if args.sample:
        print(json.dumps(SAMPLE_LISTINGS, indent=2))
        return 0

    if not args.listings:
        ap.error("--listings is required (or use --sample to get a skeleton)")

    try:
        with open(args.canonical) as fh:
            canonical = json.load(fh)
        with open(args.listings) as fh:
            listings = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if not isinstance(listings, list):
        print("ERROR: listings JSON must be a list of listing objects",
              file=sys.stderr)
        return 3

    report, summary = build_report(canonical, listings)
    print(json.dumps(summary, indent=2) if args.output == "json" else report)

    if summary["critical_issues"]:
        return 2
    return 1 if summary["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
