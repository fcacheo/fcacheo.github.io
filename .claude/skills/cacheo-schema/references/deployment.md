# Where this schema can actually go

Read this before generating anything. The generic version of this skill assumes
the business controls its own website's `<head>`. **Cacheo does not**, and that
changes what the output is for.

## The constraint

The agency's web presence is a Farmers corporate agent page
(`agents.farmers.com/...`) plus the Google Business Profile. Neither accepts
custom JSON-LD:

- **The Farmers agent page** is corporate-controlled. There is no `<head>`
  access, no CMS, no tag manager. Farmers publishes its own schema sitewide;
  the agency cannot add to it or override it.
- **Google Business Profile** is not a webpage and takes no markup. GBP *is*
  the structured data Google uses for local — the fields in the dashboard are
  the schema. Filling GBP out completely does the job that `InsuranceAgency`
  markup would do on an owned site.

So: **do not hand over JSON-LD as though it can be pasted somewhere today.**
Saying "add this to your site's head" would be advice the agency cannot act on.

## What the output is actually for

**1. GBP field parity (available now).** Generate the JSON-LD, then use it as
the checklist for the GBP dashboard. Every field the schema carries — hours,
service areas, languages, the service list — has a GBP equivalent. A field
populated in the schema but blank in GBP is a real, fixable gap. This is the
highest-value use today.

**2. AEO fact block (available now).** `--type fact-sheet` emits the same facts
as plain text. This is what `monthly-content-batch` calls AEO field copy and
what `ai-seo` wants machine-readable: a dense, unambiguous, consistently-worded
statement of who the agency is, where it is, and what it writes. LLMs extract
facts from text far more often than they parse JSON-LD. Keep the fact block
identical everywhere it appears — directory bios, social profiles, email
footers. Consistency is the signal.

**3. Ready for an owned surface (when one exists).** If the agency ever stands
up a landing page it controls, the JSON-LD is generated and validated and drops
straight in. Until then this is preparation, not deployment.

## If an owned page does appear

Placement: inline `<script type="application/ld+json">` in `<head>`. Use
`--html` to get it wrapped. One `InsuranceAgency` node per page; do not repeat
it on every page of a multi-page site — put it on the contact or home page and
reference it.

Validate before shipping:
1. `python3 scripts/schema_generator.py --validate rendered.json`
2. Google Rich Results Test — pastes as code, no URL needed
3. Schema.org validator for spec conformance

## What not to do

- **Do not mark up an agents.farmers.com URL as `url` on a node hosted
  elsewhere** without checking it resolves. A broken `url` is worse than none.
- **Do not invent an aggregateRating.** Review markup for reviews the agency
  did not collect on its own surface is a Google policy violation, and
  self-serving review markup is ignored anyway.
- **Do not add hours the GBP listing does not show.** The generator omits
  "Saturday by appointment" rather than guessing clock times, deliberately —
  schema that contradicts GBP is exactly the drift `cacheo-local-seo` exists to
  catch.
- **Do not use `LocalBusiness` when `InsuranceAgency` fits.** It is a real
  schema.org subtype and the more specific type is the better signal.
