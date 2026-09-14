---
name: landing-funnel-change
description: Changes 학원콕's landing page (`/`) — CTA labels and destinations, copy constants, the Kakao channel CTA, and click-event instrumentation — without breaking the repo's copy-source, event-contract, accessibility, and no-diagnosis guardrails. Use when a task moves or relabels a landing or sticky CTA, changes where `/` sends traffic, edits landing copy, touches the redirects for retired routes, or adds or removes a click event.
disable-model-invocation: true
---

# Landing funnel change (`/`)

This funnel has been rewritten many times in a few weeks (see `docs/decision-log.md` and
`docs/decisions/`). The code is fine; what breaks is the **surrounding contract** — copy
lives in data modules, frontend regressions are asserted from pytest, and the click-event
contract spans backend, frontend, docs, and tests.

**Current shape (2026-09-14):** `/` is one hero CTA → `/app`, a Groundwork section, and the
always-visible Kakao channel bar. `/check` (1분 학원 점검) and `/checklists` (상담 전 질문)
were **retired** together with the home situation cards and redirect (307) to `/app` from
`frontend/next.config.ts` — see
`docs/decisions/2026-09-14-retire-check-and-checklists.md`. Don't bring the pages, the
cards, or their events back without a new decision.

This skill is the checklist for that contract. It does not decide product direction —
that is the Founder's call, recorded in `docs/decisions/`.

## Triggers

Use when a task does any of:

- moves, relabels, or re-points a CTA on `/` (hero, `GroundworkSection`, `StickyKakaoBar`, footer)
- changes which route is the primary conversion for organic or paid traffic
- edits `landingFacts.ts`
- adds, renames, or removes a `click_logs` event
- adds, removes, or changes the redirects for retired routes in `frontend/next.config.ts`

## Do NOT use when

- the work is in `/app` (the recommendation shell), `AppShell`, `ChatPanel`, `MapPanel`
- the work touches recommendation APIs, ranking, `services/scoring.py`, or academy JSON
- it is consultation-question wording — that lives in the backend
  (`app/prompts/consultation.py`, `app/services/consultation_service.py`) behind
  `POST /consultation/questions`
- it is a pure visual/token change with no copy, destination, or event change
  (`docs/design/theme.md` governs that)
- the ask is to write or place ad copy on an external platform — out of repo scope

## Read first

1. `AGENTS.md` §5 (product scope) and §7 (the load-bearing rules)
2. The **3 most recent decisions** — the last files in `docs/decisions/` (names sort by date;
   if there are fewer than 3, also the top of the archived `docs/decision-log.md`). This funnel's decisions supersede
   each other frequently; an entry from last week may already be dead.
3. The route roles sentence in `AGENTS.md` §5 — it names `/`'s primary CTA and the retired
   routes in prose. If you change either, that sentence goes stale and must be updated too.

---

## Rule 1 — Copy lives in data modules, never in JSX

| Route | Copy source of truth |
|---|---|
| `/` | `frontend/src/components/landing/landingFacts.ts` |
| `/app` | `frontend/src/components/app/exploreCopy.ts` |

Never inline a new CTA label or reassurance line into `LandingPage.tsx` / `PageHero.tsx` /
`StickyKakaoBar.tsx`. Export a constant and import it.

Two traps:

- **The home hero mirrors `/app`.** `HOME_HEADLINE` / `HOME_SUPPORT` / `HOME_CTA_LABEL` say
  the same thing as `exploreCopy`'s `FORM_HEADING` / `FORM_SUPPORT` / `SUBMIT_LABEL`, and the
  trust line is imported from `exploreCopy.TRUST_NOTE` rather than duplicated. Change them
  together, or the parent lands on `/app` and reads a different promise.
- **`CTA_REASSURANCE` describes the Kakao channel modal** (`KakaoChannelModal.tsx`,
  opened by every `KakaoChannelCta`), not a generic promise —
  `"무료 · 이름/연락처 입력 없음 · 언제든 차단 가능"`. Reusing this line under a button
  that does something else states something false. Every reassurance line must be true of
  what *that* button actually does, verified against the implementation.

## Rule 2 — There is no frontend test runner

`frontend/package.json` scripts are `dev`, `build`, `start`, `lint`. No jest, vitest,
or playwright — and a copy change is not the moment to introduce one.

Frontend regressions are asserted from **pytest**, by reading the `.ts` files as text:

- `tests/test_landing_copy.py` — `MISA_ACADEMY_COUNT` vs `data/academies/*.json`, home CTA
  → `/app`, Kakao modal-first, and the retired routes / events / copy guards
- `tests/test_app_explore_copy.py` — `/app` copy contract and the landing → `/app` link

Extend those files. When you add a CTA destination or an event, add an assertion for it.
A destination regression is invisible to `npm run build`.

## Rule 3 — The click-event contract spans six places

Adding or removing one event means editing all of these, in one change:

1. `backend/app/core/constants.py` — `ClickEvent` enum member
2. `frontend/src/lib/types.ts` — `ClickEventType` union
3. the call site
4. `docs/api.md` — the `POST /events` `event` row **and** its 의미 column
5. `tests/test_engagement_api.py` — accepted / rejected values
6. a decision file in `docs/decisions/` — what the event means and why it exists

`click_logs.event` is a plain column, **not a DB enum** — no Alembic migration needed.
`app/schemas/engagement.py` validates requests against the `ClickEvent` enum, so step 1 is
what makes a value legal; an unknown value returns 422.

**Page views are never events.** Only explicit user actions.

### Current events

| Event | Fires where | Means |
|---|---|---|
| `phone` · `website` · `directions` · `detail` | `/app` candidate cards and detail modal | external action on a candidate |
| `kakao_channel` | `KakaoChannelLink` (only inside `KakaoChannelModal`) | Kakao channel-add click |

**Retired** (422 now; old rows stay in `click_logs`): `home_stage_*` (2026-08-19);
`mini_check_*`, `home_check_clicked`, `checklist_kakao_clicked`, `home_explore_selected`,
`explore_check_clicked`, `check_explore_clicked` (2026-09-14). Never reuse a retired name
for a new meaning — historical rows would silently mix into the new metric.

⚠️ **Never call `trackEvent` directly for a Kakao link.** `KakaoChannelLink` holds a
`trackedRef` dedupe guard; bypassing it double-counts. It always sends `kakao_channel` —
the `event` prop was removed with `checklist_kakao_clicked`. A second Kakao event needs a
decision, then all six contract edits.

Tracking must never block the user: every call site is
`trackEvent({...}).catch(() => {})`. Keep that shape.

## Rule 4 — Accessibility invariants

- **`StickyKakaoBar`** (rendered unconditionally by `SiteChrome`, shared across
  `/`·`/privacy`) is a plain always-visible `fixed` bar — no scroll sentinel, nothing to
  keep in sync. Don't reintroduce reveal-on-scroll logic without a decision record.
- **`KakaoChannelCta`** owns its own `open` boolean and renders `KakaoChannelModal`
  next to itself — every Kakao entry point (footer, `StickyKakaoBar`, `GroundworkSection`)
  gets independent modal state.
- **`Modal`** (`@/components/ui/Modal.tsx`) is the one shared a11y implementation:
  `role="dialog"`/`aria-modal`/`aria-labelledby`, a focus trap (Tab wraps inside the
  panel, Escape closes, focus returns to the trigger on close), and a portal to
  `document.body` so it isn't clipped by the sticky bar's `backdrop-filter`. Fix a11y
  bugs here, once, rather than in each modal usage.

**Navigation uses a real `href`**, not `onClick` + `router.push`. Middle-click,
open-in-new-tab, and prefetch all depend on it.

The component for this already exists: **`ButtonLink`** from `@/components/ui` — a
`next/link` carrying `buttonClassName()`, so a link-CTA looks identical to a `Button`
with no new styles and no `<button>` nested in an `<a>`. The home hero CTA in
`LandingPage.tsx` (`HomeHero`) is the reference usage. Do not hand-roll a styled `<Link>`,
and do not add an `as`/`asChild` prop to `Button`.

Hero animations are gated on `prefers-reduced-motion` — keep new elements consistent
with the existing `hero-fade-up` classes.

## Rule 5 — Content guardrails (this is the product's ethics line)

**Never produce:**

- an academy quality score, grade, rank, or good/bad verdict
- a recommendation to switch academies
- a student achievement diagnosis, score prediction, or school-exam analysis
- coercive or diagnostic phrasing: `반드시 제공해야`, `진짜 원인`, `판정`, `교체해야`
- fear framing about the academy's motives

**Always:**

- frame output as **counseling preparation** — questions the parent can ask
- present results as `조건과 관련해 확인해 볼 후보 정보`, never 확정 추천·순위·별점
- any number in copy must trace to `data/academies/*.json`. Unverified → `null`, never
  a heuristic.

A static self-check quiz on the landing (`/check`) was retired on 2026-09-14 — situation
input and questions now go through `/app`. Don't reintroduce one without a decision.

## Rule 6 — Decision record supersede protocol

Add a **new** file `docs/decisions/YYYY-MM-DD-slug.md` (template and supersede rules live in
`docs/decisions/README.md`). `docs/decision-log.md` is archived through 2026-09-13 — never append to it.
Never edit or delete an older decision's body — the record's value is showing what was believed when.

State explicitly:

- **계기** — what changed to justify reopening a settled decision
- **결정** — the new rule
- **무엇을 대체하는가** — name the superseded decision: link its file, or give date and title if it is in the archived log
- **경로** — the route → role table after the change
- **계측** — which event measures the new conversion
- **바꾸지 않은 것** — the scope you deliberately left alone

Then propagate: `docs/api.md` if events changed, `AGENTS.md` §5 if route roles changed.

---

## Auditing the page (companion skill, scoped)

`landing-page-conversion-audit` is installed for reviewing layout, hierarchy, and copy.
It is an **e-commerce checkout-funnel** skill, so use only part of it:

- **Apply** §A message match (does `/`'s headline repeat the ad's promise in the ad's
  own words), §B above-the-fold on 390×844 (**count the competing CTAs** — this page
  runs one primary CTA to `/app` plus the Kakao channel CTA by design), §C offer clarity
  in 5 seconds, §G is a conversion event firing at all.
- **Skip** §D forms, §E payment trust, §F upsells. This page has no checkout, no
  form, and no price. Its sibling-skill references (`sales-funnel-blueprint`,
  `post-purchase-upsell-flow`, `server-side-conversion-tracking`) are not installed.
- **Ignore the whole "Implementing the fixes" section.** It advertises the author's own
  self-hosted funnel builder (Docker, Cloudflare Workers). Out of scope here, and
  deploying is never in scope for a funnel copy change.
- **Reject any finding built on urgency, scarcity, risk-reversal, or fear framing**, no
  matter how it ranks. Rule 5 outranks the audit. Report it as considered-and-declined
  rather than silently dropping it.

Two of its reporting rules are worth keeping verbatim: never claim a percentage lift for
a fix, and under ~1,000 sessions / ~30 conversions say plainly that the data cannot
separate signal from noise. The Danggeun numbers in `decision-log.md` (≈600 impressions,
2 clicks) are squarely in that regime — treat them as direction, never as measurement.

## Workflow

1. Read `AGENTS.md` §5/§7 and the 3 most recent decisions (`docs/decisions/`, then the archived
   `decision-log.md` top if needed). Name the decision this
   change supersedes, if any.
2. Read the touched components **and** their copy modules before editing.
3. Grep the event names involved across `.py`, `.ts`, `.tsx`, `.md` — confirm each
   name's real meaning at its call site, not from the name.
4. Make copy changes in the data module; components import.
5. Wire destinations with `next/link`; keep the sticky-bar and modal a11y behaviour.
6. If an event is added or removed, do all six contract edits together.
7. Extend `tests/test_landing_copy.py` (and `tests/test_app_explore_copy.py` if the `/app`
   link or mirrored copy changes) for the new destination, label, or event.
8. Write the decision file in `docs/decisions/`; propagate to `api.md` / `AGENTS.md`.
9. Validate (below). Report honestly what ran and what didn't.

## Validation

```bash
cd frontend && npm ci && npm run build
cd backend && uv sync && uv run pytest ../tests
```

Both must run. `npm run build` catches TypeScript and route errors but **cannot** catch
a wrong CTA destination or a mislabelled event — that is what the pytest copy tests are
for, which is why step 7 is not optional.

**Behaviour the copy tests still cannot see** — the Kakao modal's focus trap and
Escape-to-close, focus returning to the trigger on close, the hero CTA really navigating
to `/app`, the retired URLs really landing on `/app` — use the **`webapp-testing`** skill
(installed in this repo) to drive `npm run dev` with an ad-hoc Playwright script. Run it
whenever a change touches `Modal.tsx`, `KakaoChannelCta`, a CTA destination, or the
redirects. Those scripts are throwaway verification: never add Playwright to
`frontend/package.json`.

If `npm ci` fails on a lockfile mismatch: report the failing command, the error summary,
and whether you verified another way. Do **not** bulk-update dependencies to get green.
Leave no build artifacts behind.

Do not deploy, push, or commit unless explicitly asked.

## Common failure modes

| Symptom | Cause |
|---|---|
| `422` on a new event | added to `types.ts` but not to `ClickEvent` enum |
| Modal focus escapes to the page behind it | bypassed `Modal.tsx` with a hand-rolled overlay instead of reusing it |
| Reassurance line promises something false | reused `CTA_REASSURANCE` under a new destination |
| `test_landing_copy` fails on the academy count | `MISA_ACADEMY_COUNT` no longer matches `data/academies/*.json` |
| `test_check_and_checklists_are_retired_and_redirect_to_app` fails | a retired route or component came back, the redirect was removed or made permanent, or something links to `/check`·`/checklists` again |
| Reviewer asks "what happened to the old decision?" | edited an old decision's body instead of superseding it with a new decision file |
