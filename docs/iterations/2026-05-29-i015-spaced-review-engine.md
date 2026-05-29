# 2026-05-29 I-015 Spaced Review Engine

## Goal

Make the daily review queue schedule future review work instead of acting only as a low-mastery list.

## Optimization Direction

Learning retention and product function. This iteration makes the review loop more useful for heavy users by recording when a card was reviewed, how many times it has been reviewed, and when it should appear again.

## Scope

- Add review scheduling fields to study cards:
  - `review_count`
  - `last_reviewed_at`
  - `next_review_at`
- Add an Alembic migration for existing private deployments.
- Schedule the next review when mastery is updated:
  - `忘记` / mastery 1: next day.
  - `模糊` / mastery 2: two days later.
  - mastery 3: three days later.
  - `掌握` / mastery 4: three days later.
  - `简单` / mastery 5: seven days later.
- Make the daily queue show only due unscheduled or due scheduled cards.
- Keep low-mastery counts across all cards, even when a card is scheduled for a future date.
- Show next-review labels and review counts in the progress panel.

Deferred:

- Per-course review goals and streaks.
- User-configurable intervals.
- Full SM-2 style ease-factor scheduling.
- Wrong notes as first-class scheduled review items.

## Markdown Updates

- `docs/iterations/2026-05-29-i015-spaced-review-engine.md`
- `docs/professional-release-roadmap.md`
- `docs/user-guide.md`
- `README.md`

## Acceptance Gates

- `cd backend && E:\DevMemory\.venv\Scripts\python.exe -m pytest tests`
- `cd frontend && npm.cmd test`
- `cd frontend && npm.cmd run build`
- Production prompt/confirm scan stays clean.
- Production mojibake scan stays clean.
- `git diff --check`

## Follow-up

Next recommended iteration: I-016 Course Dashboard. The next product step is to make the opening screen answer "what should I study now?" using due reviews, failed documents, recent questions, and weak areas.
