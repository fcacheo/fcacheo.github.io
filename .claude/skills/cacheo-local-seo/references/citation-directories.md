# Citation Directories — Cacheo Insurance Agency

A "citation" is any listing of the agency's name, address, and phone. Google
uses agreement across these as a trust signal for the Map Pack. The goal is not
maximum listings; it is **zero contradictions** across the listings that exist.
Ten perfect citations beat sixty with three phone numbers between them.

## Tier 1 — fix within the week

| Directory | Why it is Tier 1 | Notes |
|---|---|---|
| Google Business Profile | Directly drives Map Pack rank | The single highest-leverage asset |
| Farmers agent locator | Syndication source | Corporate-controlled; see below |
| Apple Maps (Business Connect) | Powers Siri and iPhone Maps | Frequently unclaimed by agencies |
| Bing Places | Feeds Bing, Copilot, and Duck Duck Go | Cheap to claim, rarely done |

**The Farmers locator is the special case.** The agency does not own that
record — corporate does. Data aggregators pull from it, so an error there
re-infects directories you already corrected by hand. When the checker flags a
Tier 1 mismatch on `farmers_agent_locator`, the fix is a request through the
Farmers agency-support channel, not an edit. Log the request date; re-check in
30 days. Do not fix the downstream directories first — they will drift back.

## Tier 2 — fix within the month

| Directory | Notes |
|---|---|
| Yelp | Prospects read it even when it does not rank |
| Better Business Bureau | Trust signal for the older end of the book |
| Facebook Page | Also the Podium/review surface for some prospects |
| Nextdoor | Genuinely strong for a Long Beach neighborhood audience |

## Tier 3 — fix opportunistically

Yellow Pages, Superpages, Manta, Chamber of Commerce, insurance.com. Low
traffic, but they are cheap to correct and they feed the aggregators. Do not
spend a morning here while a Tier 1 is red.

## What counts as a mismatch

- **Name:** "Farmers Insurance - Francisco Cacheo" vs "Francisco Cacheo
  Agency" vs "Cacheo Insurance." Pick the canonical form and hold it.
  Descriptors appended to the name ("Long Beach Auto Insurance") violate GBP
  policy and can trigger suspension — do not add them anywhere.
- **Phone:** any digit difference. A tracking number that differs from the
  canonical is a mismatch even when it forwards correctly.
- **Address:** suite number missing is the most common real-world error.
  "Ste 450" vs "Suite 450" vs "#450" is *not* a mismatch — the checker
  normalizes those.
- **Hours:** "Sat by appointment" is often stored as "Closed Saturday," which
  costs weekend Map Pack impressions. Worth fixing.

## Collecting listing data for the checker

`nap_checker.py` does not browse — you collect, it diffs. Start from the
skeleton:

```bash
python3 scripts/nap_checker.py --sample > listings.json
```

Fill each entry from what the directory actually shows — copy the values
exactly as displayed, including the errors. Do not normalize by hand; that is
the script's job and hand-normalizing hides the very drift you are looking for.
Set `"listed": false` for a directory with no listing at all.
