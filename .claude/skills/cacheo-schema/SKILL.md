---
name: cacheo-schema
description: >
  Structured data (JSON-LD) and machine-readable fact blocks for Cacheo
  Insurance Agency. Use when the task involves "schema markup", "JSON-LD",
  "structured data", "rich results", "InsuranceAgency schema", "FAQ schema",
  "make our info machine-readable", or checking that the Google Business
  Profile carries every field it should. NOT for AI citation strategy or
  llms.txt (use ai-seo). NOT for directory listings, NAP consistency, or review
  responses (use cacheo-local-seo). NOT for rank tracking or the monthly report
  (use seo-audit-report).
metadata:
  version: 1.0.0
  adapted_from: alirezarezvani/claude-skills schema-markup + local-seo-manager (MIT)
---

# Structured Data — Cacheo Insurance Agency

Generates schema.org JSON-LD and a plain-text fact block from the canonical
NAP, so every machine-readable statement of the agency's facts comes from one
file and cannot drift.

**Read `references/deployment.md` before generating anything.** The agency does
not control its website's `<head>` — the Farmers agent page is corporate, and
GBP takes no markup. That does not make this skill useless, but it does change
what the output is for, and handing someone JSON-LD to "paste into your site"
would be advice they cannot act on.

**Canonical facts:** `../cacheo-local-seo/assets/cacheo-nap.json`. That file is
the master; this skill reads it and never writes it. If the agency's details
change, edit it there and regenerate here.

---

## Mode 1 — GBP field parity check (the one that pays today)

```bash
python3 scripts/schema_generator.py --type insurance-agency
```

Then walk the generated node field by field against the GBP dashboard. Every
schema field has a GBP equivalent: `openingHoursSpecification` → hours,
`areaServed` → service areas, `makesOffer` → services, `availableLanguage` →
languages. Report each field that is populated in the schema and blank or
different in GBP. Those are real gaps and they are fixable this week.

Note what the generator deliberately omits: days without clock times. Saturday
is "by appointment," so it produces no `OpeningHoursSpecification` rather than
an invented 09:00–13:00. Do not add one.

---

## Mode 2 — AEO fact block

```bash
python3 scripts/schema_generator.py --type fact-sheet
```

Emits the same facts as dense plain text. LLMs extract from prose far more
reliably than they parse JSON-LD, so this is the format that actually moves AI
visibility. Use it as the canonical wording for directory bios, social profile
descriptions, and the AEO field copy in `monthly-content-batch`. Identical
wording everywhere is the point — variation reads as uncertainty.

---

## Mode 3 — Generate and validate JSON-LD

```bash
python3 scripts/schema_generator.py --type insurance-agency --html
python3 scripts/schema_generator.py --type person
python3 scripts/schema_generator.py --type faq --faqs faqs.json
python3 scripts/schema_generator.py --validate rendered.json
```

`--faqs` takes a JSON list of `{"question": ..., "answer": ...}`. Source the
questions from what people actually ask the office, not from keyword tools —
FAQ schema earns nothing when the questions are invented.

Every generation self-validates. Exit `2` means the output printed but failed
validation; read the errors on stderr before using it. The generator warns on
stderr while any canonical field is still marked `_unverified`.

If an owned landing page ever exists, `references/deployment.md` covers
placement and the pre-ship validation chain. Until then, treat JSON-LD output
as prepared, not deployed, and say so.

---

## Boundaries

Generates and validates markup; does not audit rankings, does not write
content, does not touch directory listings. If the request is really about
whether AI assistants recommend the agency, that is `ai-seo` — hand it over by
name rather than answering half of it here.
