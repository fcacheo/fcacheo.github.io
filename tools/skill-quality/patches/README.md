# daily-az-report.diff

Three changes to the `daily-az-report` skill. Enhancements only — on a healthy
run the briefing output is byte-identical.

Apply by uploading the edited `SKILL.md` in claude.ai → Settings → Capabilities
→ Skills (custom skill `skill_01WVC6bGsd9enCmLcuehQM8r`). This diff is kept
here so the change is reviewable; it is not applied automatically.

## 1. Login click by selector, not coordinate (Step 1.4)

`Click the Login button at approximately (810, 538)` only lands correctly when
the window size, zoom, and banner state match whenever that coordinate was
measured. Otherwise it clicks empty space, waits 3s, and fails the title check.
Replaced with a `button[type="submit"]` lookup, falling back to a button whose
text matches `/log ?in|sign ?in/i`, and throwing `LOGIN_BUTTON_NOT_FOUND` when
neither is present.

The selector is unverified against the live AgencyZoom login page — it matches
the common SPA patterns. If it misses, the thrown error names the problem,
which the coordinate click did not.

## 2. `monthlyGoal` fails to `N/A` (Step 2a)

It previously fell back to `'30,000'`, so a failed extraction produced a real-
looking goal figure while every neighbouring field showed `N/A`. Now fails to
`N/A` like the rest, which also makes it legible to the Step 2.5 gate.

## 3. Step 2.5 result-validation gate (new, before Step 3)

Blocks the send when extraction failed, rather than emailing a briefing full of
`N/A` that reads as a quiet day.

Counts `'N/A'` sentinels, never zeros — `achievedToday: '0'` before the first
sale of the day is a real value, and a naive zero check would block every
morning run. Trips on: login not reaching My Dashboard, >=60% of dashboard
fields `N/A`, or an empty YTD leaderboard or daily sales table.

Verified against three cases:

| Case | Result |
|---|---|
| Healthy 7am run, nothing sold yet, real zeros | sends |
| Two dashboard tiles missing, rest fine | sends |
| Failed extraction, 8/9 fields `N/A`, empty tables | **blocked** |

Partial degradation still sends by design; only a genuinely broken run is held.

## Not changed

The hardcoded credential at Step 1 is untouched — removing it requires deciding
how the report authenticates, which is a separate change. Rotating the
AgencyZoom password will break this login until that is resolved.
