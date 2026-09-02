# skill-descriptions.diff

Rewrites the frontmatter `description` of `daily-az-report` and
`weekly-pipeline-report`. Frontmatter only — no step, selector, or output
change in either skill. The briefings they produce are unaffected.

Apply by uploading each edited `SKILL.md` in claude.ai → Settings →
Capabilities → Skills. This diff is kept here so the change is reviewable; it
is not applied automatically.

## Why

`skill-originality.py` scored these two at **20.0% trigger overlap**, at the
fail threshold, the only failing pair across the ten-skill collection:

```
!!  20.0%  daily-az-report  <->  weekly-pipeline-report
1 at/above FAIL, 45 pairs compared
```

The cause was not two skills claiming the same triggers. Their distinctive
phrases were already distinct — "generate the ops briefing" versus "which leads
are stuck". The cause was shared template scaffolding: 25 shared 4-grams,
nearly all of it boilerplate.

```
use this skill whenever the ... the task involves running the
also triggers when the user ... hands you a scheduled task file named
docx generation html email send ... generates the cacheo insurance agency
```

The frontmatter description is the text the model reads when choosing a skill.
When most of two descriptions is identical process wording, the words that
actually distinguish them carry proportionally less weight.

## What changed

**Cut the shared scaffolding.** "Use this skill whenever the task involves:",
"Also triggers when the user hands you a scheduled task file named X or asks
to", and the trailing workflow line all said the same thing in both skills.

**Cut the delivery mechanism.** Both ended with `DOCX generation → HTML email
send`. Both do that, so it never distinguished them — it is real information
about the skill, but it belongs in the body, not in the routing text.

**Added explicit negative routing.** Each description now names the skills it
is *not*, in the `NOT for X (use Y)` form already used by `ai-seo`,
`cacheo-local-seo`, and `cacheo-schema`.

**Added the missing question each answers.** `daily-az-report` is a single
day's production snapshot; `weekly-pipeline-report` answers which leads have
sat too long in a stage and who owns them. Neither said so plainly.

## A caveat about the metric

Negative routing clauses are the thing that most prevents misfires, and they
necessarily share vocabulary — `NOT for retention or churn (use
quarterly-retention-report)` reads almost identically in any skill that needs
it. A first pass at this rewrite scored 12.8%, still above warn, and the entire
residual was those clauses plus the shared delivery phrase.

So the metric penalizes part of the fix. Do not optimize the number by deleting
disambiguation. What came out here was the delivery-mechanism phrasing, which
helps no routing decision at all; the `NOT for` clauses stayed, and the score
landed at 5.3% anyway.

## Result

```
5.3%  daily-az-report  <->  weekly-pipeline-report
0 at/above FAIL, 0 at/above WARN, 45 pairs compared      exit 0
```

Verified across the full ten-skill collection, not just the pair: no new
overlap was introduced against `agencyzoom`, `quarterly-retention-report`,
`phone-report`, `seo-audit-report`, `monthly-content-batch`, `ai-seo`,
`cacheo-local-seo`, or `cacheo-schema`. Every remaining pair sits below the
warn threshold, the highest being 5.3%.

Body overlap was 0.0% before and after; these are frontmatter-only edits.
