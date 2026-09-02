# Cacheo skills

Two skills adapted for Cacheo Insurance Agency, kept here because this is the
only durable git repository available — the account's synced skills directory
is platform-managed and cannot be written to from a session.

| Skill | Does |
|---|---|
| `cacheo-local-seo` | NAP consistency across directories, citation gaps, review responses |
| `cacheo-schema` | JSON-LD generation, GBP field parity, AEO fact block |

`cacheo-local-seo/assets/cacheo-nap.json` is the single source of facts for
both. Edit it there; `cacheo-schema` reads it and never writes it. If it and
`CLAUDE.md` in the Cacheo Agency workspace disagree, `CLAUDE.md` wins.

Four fields in that file are marked `_unverified` (website slug, service areas,
primary category, service list). Both tools warn while any remain. Confirm them
against `CLAUDE.md` or the live listings, then remove them from the list.

## Installing

These are project skills — a Claude Code session in this repository picks them
up automatically. To use them in the Cacheo Agency workspace, upload each skill
directory through the skills settings on the account, the same way the existing
custom skills (`agencyzoom`, `seo-audit-report`, `monthly-content-batch`) got
there.

## Provenance

Adapted from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)
(MIT, © 2025 Alireza Rezvani) — `marketing-skill/skills/local-seo-manager` and
`marketing-skill/skills/schema-markup`. Both scripts were substantially
rewritten; the upstream headers name the changes.

## Trigger boundaries

Written to not collide with the existing Cacheo skills:

- rank tracking, GBP content audit, monthly report → `seo-audit-report`
- GBP posts, social, email, AEO copy → `monthly-content-batch`
- AI/LLM citation strategy, llms.txt → `ai-seo`
- listings, NAP, reviews → `cacheo-local-seo`
- JSON-LD, structured data → `cacheo-schema`
