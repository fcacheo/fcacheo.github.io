# skill-quality

Quality checks for the Cacheo Claude Code skill collection.

Ported and adapted from [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)
(MIT), whose `scripts/check-agent-originality.sh` performs the same kind of
duplicate detection across an agent roster.

## skill-originality.py

Flags skills that duplicate each other, on two independent signals:

- **BODY** — 8-word shingle Jaccard over the `SKILL.md` body, with cadence and
  domain proper nouns neutralized so a find-replace re-skin (`daily` → `weekly`,
  `Auto` → `Home`) cannot hide the copy.
- **TRIGGER** — 4-word shingle Jaccard over the frontmatter `description`. This
  is the text the model reads when choosing a skill, so overlap here predicts
  the wrong skill firing.

They mean different things. High BODY between two report skills usually means
shared scaffolding worth extracting into a helper. High TRIGGER is the one that
causes user-visible wrong behavior.

```bash
./skill-originality.py --skills-dir ~/.claude/skills
./skill-originality.py path/to/a/SKILL.md path/to/another/SKILL.md
./skill-originality.py --skills-dir ~/.claude/skills --json overlap.json
```

Exit status is 1 if any pair is at or above a fail threshold, so it can gate CI.

### Thresholds

Defaults are `--body-warn 15 --body-fail 35 --trigger-warn 8 --trigger-fail 20`.
Calibrate against your own baseline before trusting them: across the eight
Cacheo-authored skills the observed maximum body overlap is 5.8% and the
maximum trigger overlap 16.4%, so the current defaults leave real headroom.

### Known gap

Shingle overlap does not catch two skills claiming the *same short quoted
trigger phrase* when the surrounding wording differs — that scores near zero
while being a genuine collision. Check exact quoted phrases separately.
