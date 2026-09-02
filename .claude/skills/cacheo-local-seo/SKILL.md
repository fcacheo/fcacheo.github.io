---
name: cacheo-local-seo
description: >
  Local listing hygiene for Cacheo Insurance Agency — NAP consistency across
  directories, claiming and correcting citations, and writing Google review
  responses. Use when the task involves "check our listings", "NAP
  consistency", "is our address wrong on Yelp", "claim our Bing/Apple Maps
  listing", "respond to this review", "answer our Google reviews", "our phone
  number is wrong online", or auditing where the agency is listed. NOT for the
  monthly SEO report or rank tracking (use seo-audit-report). NOT for AI/LLM
  citation strategy (use ai-seo). NOT for writing GBP posts, social captions,
  or emails (use monthly-content-batch). NOT for structured data or JSON-LD
  (use cacheo-schema).
metadata:
  version: 1.0.0
  adapted_from: alirezarezvani/claude-skills local-seo-manager (MIT)
---

# Local Listing Hygiene — Cacheo Insurance Agency

Two jobs live here, and neither belongs to the monthly report: keeping the
agency's name, address, phone, and hours identical everywhere they appear, and
answering reviews within 48 hours without creating compliance exposure.

**Canonical NAP** (the values every check compares against):
`assets/cacheo-nap.json`. Edit that file first if anything about the agency
changes, then re-run. If it and `CLAUDE.md` in the Cacheo Agency workspace ever
disagree, **`CLAUDE.md` wins** — update the asset to match.

Four fields in the asset are marked `_unverified` — the website slug, service
areas, primary category, and service list. Confirm them against `CLAUDE.md` or
the live listing on first use, then remove them from the `_unverified` list.
The checker prints a warning while any remain.

---

## Mode 1 — NAP consistency audit

Run when: the user asks about listings, or quarterly as maintenance, or after
anything about the agency changes (a phone number, a suite, the hours).

**Step 1 — get the skeleton.**
```bash
cd .claude/skills/cacheo-local-seo
python3 scripts/nap_checker.py --sample > listings.json
```

**Step 2 — collect, do not normalize.** Visit each directory in
`references/citation-directories.md` and copy what it actually displays into
`listings.json`, errors included. Hand-normalizing as you go hides the drift
you are looking for. Set `"listed": false` where no listing exists.

**Step 3 — diff.**
```bash
python3 scripts/nap_checker.py --listings listings.json
```
Exit codes: `0` clean · `1` mismatches, none critical · `2` at least one Tier 1
· `3` bad input. Use `--output json` to feed another step.

**Step 4 — report in fix order, not directory order.** Tier 1 first. For each
issue give the directory, the wrong value, the right value, and who can change
it. Then stop — do not also propose content ideas, that is
`monthly-content-batch`.

**The Farmers locator exception:** a Tier 1 mismatch on
`farmers_agent_locator` is a corporate record the agency cannot edit. The fix
is a support request, and downstream directories will drift back until it
lands. Say so plainly rather than listing it as a normal to-do.

---

## Mode 2 — Review responses

Run when: the user pastes a review, or asks to catch up on unanswered reviews.

Read `references/review-responses.md` in full before drafting. It carries five
compliance rules that override tone, structure, and everything else — the short
version is that a public response must never confirm someone is a customer,
never touch a claim or a premium, and never give coverage advice.

Draft, then run the pre-publish checklist at the bottom of that reference
against every response before handing it over. Match the reviewer's language:
the agency serves a bilingual book, and a Spanish review gets a Spanish reply.

Present drafts for approval. **Do not post anything to Google.** Posting is a
person's decision on a person's account.

---

## Mode 3 — Citation gap check

Run when: asked where the agency should be listed, or after Mode 1 turns up
several `not listed` rows.

Work `references/citation-directories.md` top down. Report which Tier 1 and
Tier 2 directories have no listing, what claiming each requires (postcard,
phone verification, corporate request), and the order to do them in. Zero
contradictions across ten listings beats sixty listings with three phone
numbers between them — do not recommend bulk citation building.

---

## Boundaries

This skill does not track rankings, does not audit the GBP profile's content or
posting cadence, and does not write posts. Rankings and the GBP content audit
belong to `seo-audit-report`; posts belong to `monthly-content-batch`. If a
request spans both, do the listing half here and hand the rest over by name.
