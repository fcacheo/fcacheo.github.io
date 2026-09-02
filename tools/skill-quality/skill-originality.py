#!/usr/bin/env python3
"""
skill-originality.py — Flag Claude Code skills that substantially duplicate
each other, in body content or in trigger description.

Ported from msitarzewski/agency-agents scripts/check-agent-originality.sh (MIT),
adapted from that repo's agent roster to a SKILL.md collection.

Two independent signals:

  BODY        8-word shingle Jaccard over the SKILL.md body, with cadence and
              domain proper nouns neutralized so a find-replace re-skin
              ("daily" -> "weekly", "Auto" -> "Home") cannot hide the copy.

  TRIGGER     4-word shingle Jaccard over the frontmatter `description` only.
              This is the field the model actually reads when choosing a skill,
              so overlap here predicts misfires — the wrong skill firing, or two
              skills both looking correct for one request.

Body overlap and trigger overlap mean different things. High BODY between two
report skills is usually shared scaffolding (login -> extract -> DOCX -> email),
which argues for extracting a common helper, not rewriting. High TRIGGER is the
one that causes user-visible wrong behavior.

Usage:
  ./skill-originality.py [--skills-dir DIR] [--json OUT.json] [file ...]

Exit status:
  0  nothing at/above the fail threshold
  1  at least one pair at/above a fail threshold
"""

import argparse
import json
import os
import re
import sys
from itertools import combinations

# Tokens swapped in a plausible re-skin of an existing skill. Neutralized before
# comparison so the copied structure underneath stays visible. Extend as the
# skill collection grows into new cadences, lines of business, or data sources.
ENTITY = re.compile(
    r'\b(daily|weekly|monthly|quarterly|annual|annually|yearly|'
    r'january|february|march|april|may|june|july|august|september|october|'
    r'november|december|'
    r'commercial|auto|home|life|fire|umbrella|renters|condo|'
    r'briefing|pipeline|retention|churn|phone|call|seo|aeo|geo|'
    r'agencyzoom|intermedia|podium|apex|farmers|cacheo)\b')

FM_DELIM = '---'


def split_frontmatter(text):
    """Return (frontmatter, body). Body is everything after the closing ---."""
    if not text.startswith(FM_DELIM):
        return '', text
    parts = text.split(FM_DELIM, 2)
    if len(parts) < 3:
        return '', text
    return parts[1], parts[2]


def description_of(frontmatter):
    """Pull the `description:` value, including YAML block/continuation lines."""
    lines = frontmatter.splitlines()
    out, capturing = [], False
    for line in lines:
        if re.match(r'^description:', line):
            capturing = True
            out.append(re.sub(r'^description:\s*[|>]?-?\s*', '', line))
            continue
        if capturing:
            # A new top-level key ends the description block.
            if re.match(r'^[A-Za-z_][A-Za-z0-9_-]*:', line):
                break
            out.append(line.strip())
    return ' '.join(out).strip()


def tokens(text, neutralize=True):
    text = text.lower()
    if neutralize:
        text = ENTITY.sub(' ', text)
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return text.split()


def shingles(words, k):
    if len(words) < k:
        # Too short to shingle at k; fall back to the whole token set so short
        # descriptions still compare against each other rather than scoring 0.
        return {' '.join(words)} if words else set()
    return set(' '.join(words[i:i + k]) for i in range(len(words) - k + 1))


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def load_skills(paths):
    skills = {}
    for p in paths:
        try:
            with open(p, encoding='utf-8') as fh:
                text = fh.read()
        except OSError as e:
            print(f"  skip (unreadable): {p} ({e})")
            continue
        fm, body = split_frontmatter(text)
        if not fm:
            print(f"  skip (no frontmatter): {p}")
            continue
        name = os.path.basename(os.path.dirname(p))
        skills[name] = {
            'path': p,
            'description': description_of(fm),
            'body_shingles': shingles(tokens(body), 8),
            'desc_shingles': shingles(tokens(description_of(fm)), 4),
            'body_words': len(tokens(body)),
        }
    return skills


def discover(skills_dir):
    found = []
    for entry in sorted(os.listdir(skills_dir)):
        candidate = os.path.join(skills_dir, entry, 'SKILL.md')
        if os.path.isfile(candidate):
            found.append(candidate)
    return found


def band(pct, warn, fail):
    if pct >= fail:
        return 'FAIL'
    if pct >= warn:
        return 'WARN'
    return 'OK'


def report(skills, kind, key, warn, fail):
    print(f"\n{'=' * 72}\n{kind} OVERLAP   (WARN >= {warn:.0f}%, FAIL >= {fail:.0f}%)\n{'=' * 72}")
    rows = []
    for a, b in combinations(sorted(skills), 2):
        pct = jaccard(skills[a][key], skills[b][key]) * 100
        rows.append((pct, a, b))
    rows.sort(reverse=True)

    failures = [r for r in rows if r[0] >= fail]
    warnings = [r for r in rows if warn <= r[0] < fail]

    for pct, a, b in rows[:15]:
        tag = band(pct, warn, fail)
        marker = {'FAIL': '!!', 'WARN': ' *', 'OK': '  '}[tag]
        print(f"  {marker} {pct:5.1f}%  {a}  <->  {b}")
    if len(rows) > 15:
        print(f"     ... {len(rows) - 15} more pairs below {rows[15][0]:.1f}%")

    print(f"\n  {len(failures)} at/above FAIL, {len(warnings)} at/above WARN, "
          f"{len(rows)} pairs compared")
    return rows, failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*')
    ap.add_argument('--skills-dir', default=os.path.expanduser('~/.claude/skills'))
    ap.add_argument('--body-warn', type=float, default=15.0)
    ap.add_argument('--body-fail', type=float, default=35.0)
    ap.add_argument('--trigger-warn', type=float, default=8.0)
    ap.add_argument('--trigger-fail', type=float, default=20.0)
    ap.add_argument('--json', dest='json_out')
    args = ap.parse_args()

    paths = args.files or discover(args.skills_dir)
    if not paths:
        print(f"No SKILL.md files found under {args.skills_dir}")
        return 1

    skills = load_skills(paths)
    if len(skills) < 2:
        print("Need at least 2 skills to compare.")
        return 1

    print(f"Comparing {len(skills)} skills.\n")
    for n in sorted(skills):
        print(f"  {n:28s} {skills[n]['body_words']:6d} body words, "
              f"{len(skills[n]['description']):4d}-char description")

    body_rows, body_fails = report(skills, 'BODY', 'body_shingles',
                                   args.body_warn, args.body_fail)
    trig_rows, trig_fails = report(skills, 'TRIGGER', 'desc_shingles',
                                   args.trigger_warn, args.trigger_fail)

    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as fh:
            json.dump({'body': [{'pct': p, 'a': a, 'b': b} for p, a, b in body_rows],
                       'trigger': [{'pct': p, 'a': a, 'b': b} for p, a, b in trig_rows]},
                      fh, indent=2)
        print(f"\nWrote {args.json_out}")

    return 1 if (body_fails or trig_fails) else 0


if __name__ == '__main__':
    sys.exit(main())
