#!/usr/bin/env python3
"""
schema_generator.py - JSON-LD generator for Cacheo Insurance Agency.

Reads the canonical NAP (the same file cacheo-local-seo uses) and emits
schema.org JSON-LD. One source of facts, so the schema block and the listing
checker can never disagree.

Usage:
    python3 schema_generator.py --type insurance-agency
    python3 schema_generator.py --type insurance-agency --html
    python3 schema_generator.py --type faq --faqs faqs.json
    python3 schema_generator.py --type fact-sheet
    python3 schema_generator.py --validate rendered.json

Types:
    insurance-agency  InsuranceAgency + address + hours + areaServed
    person            The agent as an entity, linked to the agency
    faq               FAQPage from a questions/answers JSON
    fact-sheet        Plain-text fact block for AEO copy (not JSON-LD)

Exit codes: 0 ok · 2 validation failed · 3 bad input

Adapted from local-seo-manager/schema_generator.py in
alirezarezvani/claude-skills (MIT). Changes: InsuranceAgency type, canonical
NAP search path, hours parsing from the NAP file, fact-sheet mode, validator.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.dirname(os.path.dirname(HERE))

# The master copy lives with cacheo-local-seo. Fall back to a local copy so the
# skill still runs if the two are installed separately.
NAP_SEARCH_PATH = [
    os.path.join(SKILLS_ROOT, "cacheo-local-seo", "assets", "cacheo-nap.json"),
    os.path.join(os.path.dirname(HERE), "assets", "cacheo-nap.json"),
]

DAY_MAP = {
    "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
    "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday",
    "sunday": "Sunday",
}


def find_nap(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    for candidate in NAP_SEARCH_PATH:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "canonical NAP not found. Pass --nap PATH. Looked in:\n  "
        + "\n  ".join(NAP_SEARCH_PATH)
    )


def build_address(nap: Dict) -> Dict:
    addr = nap.get("address", {})
    return {
        "@type": "PostalAddress",
        "streetAddress": addr.get("street", ""),
        "addressLocality": addr.get("city", ""),
        "addressRegion": addr.get("state", ""),
        "postalCode": addr.get("zip", ""),
        "addressCountry": "US",
    }


def build_hours(nap: Dict) -> List[Dict]:
    """Emit openingHoursSpecification for days with real clock times.

    'by appointment' and 'closed' are deliberately omitted rather than guessed.
    Google treats a missing day as unspecified, which is honest; inventing
    Saturday hours to fill the schema would contradict the GBP listing and is
    exactly the kind of drift the NAP checker exists to catch.
    """
    out = []
    for day, value in (nap.get("hours") or {}).items():
        day_name = DAY_MAP.get(day.lower())
        if not day_name or "-" not in str(value):
            continue
        opens, closes = str(value).split("-", 1)
        out.append({
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": day_name,
            "opens": opens.strip(),
            "closes": closes.strip(),
        })
    return out


def build_insurance_agency(nap: Dict) -> Dict:
    node = {
        "@context": "https://schema.org",
        "@type": "InsuranceAgency",
        "name": nap.get("name", ""),
        "address": build_address(nap),
        "telephone": nap.get("phone", ""),
    }
    if nap.get("website"):
        node["url"] = nap["website"]
    hours = build_hours(nap)
    if hours:
        node["openingHoursSpecification"] = hours
    if nap.get("service_areas"):
        node["areaServed"] = [
            {"@type": "City", "name": city} for city in nap["service_areas"]
        ]
    if nap.get("languages"):
        node["availableLanguage"] = nap["languages"]
    if nap.get("services"):
        node["makesOffer"] = [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s}}
            for s in nap["services"]
        ]
    if nap.get("gbp_url"):
        node["sameAs"] = [nap["gbp_url"]]
    return node


def build_person(nap: Dict) -> Dict:
    name = nap.get("name", "")
    agent = name.split("-")[-1].strip() if "-" in name else name
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": agent,
        "jobTitle": "Insurance Agent",
        "telephone": nap.get("phone", ""),
        "worksFor": {
            "@type": "InsuranceAgency",
            "name": name,
            "address": build_address(nap),
        },
        "knowsLanguage": nap.get("languages", []),
    }


def build_faq(faqs: List[Dict]) -> Dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("answer", ""),
                },
            }
            for item in faqs
        ],
    }


def build_fact_sheet(nap: Dict) -> str:
    addr = nap.get("address", {})
    lines = [
        f"{nap.get('name', '')}",
        f"{addr.get('street','')}, {addr.get('city','')}, "
        f"{addr.get('state','')} {addr.get('zip','')}",
        f"Phone: {nap.get('phone','')}",
    ]
    hours = nap.get("hours") or {}
    weekday = hours.get("monday", "")
    if weekday:
        lines.append(f"Hours: Monday-Friday {weekday}, Saturday "
                     f"{hours.get('saturday', 'closed')}")
    if nap.get("services"):
        lines.append("Lines written: " + ", ".join(nap["services"]))
    if nap.get("service_areas"):
        lines.append("Serves: " + ", ".join(nap["service_areas"]))
    if nap.get("languages"):
        lines.append("Languages: " + ", ".join(nap["languages"]))
    return "\n".join(lines)


REQUIRED = {
    "InsuranceAgency": ["name", "address", "telephone"],
    "FAQPage": ["mainEntity"],
    "Person": ["name"],
}


def validate(node: Dict) -> List[str]:
    errors = []
    node_type = node.get("@type")
    if not node.get("@context"):
        errors.append("missing @context")
    if not node_type:
        errors.append("missing @type")
        return errors
    for field in REQUIRED.get(node_type, []):
        value = node.get(field)
        if not value:
            errors.append(f"{node_type}: missing required field '{field}'")
    addr = node.get("address")
    if isinstance(addr, dict):
        for field in ("streetAddress", "addressLocality", "addressRegion",
                      "postalCode"):
            if not addr.get(field):
                errors.append(f"PostalAddress: empty '{field}'")
    if node_type == "FAQPage":
        for i, q in enumerate(node.get("mainEntity") or []):
            if not q.get("name"):
                errors.append(f"Question[{i}]: empty question text")
            if not (q.get("acceptedAnswer") or {}).get("text"):
                errors.append(f"Question[{i}]: empty answer text")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="JSON-LD generator (Cacheo)")
    ap.add_argument("--type", choices=["insurance-agency", "person", "faq",
                                       "fact-sheet"])
    ap.add_argument("--nap", help="canonical NAP JSON (default: auto-detect)")
    ap.add_argument("--faqs", help="questions/answers JSON for --type faq")
    ap.add_argument("--html", action="store_true",
                    help="wrap output in a <script> tag")
    ap.add_argument("--validate", metavar="FILE",
                    help="validate an existing JSON-LD file and exit")
    args = ap.parse_args()

    if args.validate:
        try:
            with open(args.validate) as fh:
                node = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 3
        errors = validate(node)
        if errors:
            print("INVALID")
            for err in errors:
                print(f"  - {err}")
            return 2
        print("VALID")
        return 0

    if not args.type:
        ap.error("--type is required (or use --validate)")

    try:
        with open(find_nap(args.nap)) as fh:
            nap = json.load(fh)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    unverified = (nap.get("_unverified") or {}).get("fields") or []
    if unverified:
        print(f"WARNING: unverified canonical fields: {', '.join(unverified)}",
              file=sys.stderr)

    if args.type == "fact-sheet":
        print(build_fact_sheet(nap))
        return 0

    if args.type == "faq":
        if not args.faqs:
            ap.error("--faqs is required for --type faq")
        try:
            with open(args.faqs) as fh:
                node = build_faq(json.load(fh))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 3
    elif args.type == "person":
        node = build_person(nap)
    else:
        node = build_insurance_agency(nap)

    errors = validate(node)
    rendered = json.dumps(node, indent=2)
    if args.html:
        rendered = f'<script type="application/ld+json">\n{rendered}\n</script>'
    print(rendered)

    if errors:
        print("\nVALIDATION ERRORS:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
