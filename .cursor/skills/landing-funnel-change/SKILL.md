---
name: landing-funnel-change
description: Changes 학원콕's /, /check, /checklists funnel — CTA labels and destinations, copy constants, counseling questions, and click-event instrumentation — without breaking the repo's copy-source, event-contract, accessibility, and no-diagnosis guardrails. Use when a task moves or relabels a landing or sticky CTA, reroutes traffic between these three routes, edits check/checklist question copy, or adds a funnel click event.
disable-model-invocation: true
---

# Landing funnel change (`/` · `/check` · `/checklists`)

This funnel has been rewritten four times in a week (see `docs/decision-log.md`).
The code is fine; what breaks is the **surrounding contract** — copy lives in data
modules, frontend regressions are asserted from pytest, one event name already means
the opposite of what it sounds like, and the sticky bar's a11y state is spread across
four props that must stay in sync.

This skill is the checklist for that contract. It does not decide product direction —
that is the Founder's call, recorded in `docs/decision-log.md`.

## Triggers

Use when a task does any of:

- moves, relabels, or re-points a CTA on `/`, `/check`, or `/checklists`
- changes which route is the primary conversion for organic or paid traffic
- edits `landingFacts.ts`, `checkData.ts`, or `checklistsData.ts`
- adds, renames, or re-points a `click_logs` funnel event
- changes the Hero → sticky-bar reveal behaviour or the waitlist modal wiring

## Do NOT use when

- the work is in `/app` (the recommendation shell), `AppShell`, `ChatPanel`, `MapPanel`
- the work touches recommendation APIs, ranking, `services/scoring.py`, or academy JSON
- it is a pure visual/token change with no copy, destination, or event change
  (`docs/design/theme.md` governs that)
- the ask is to write or place ad copy on an external platform — out of repo scope

## Read first

1. `AGENTS.md` §5 (product scope) and §7 (the load-bearing rules)
2. `docs/decision-log.md` — the **top 3 entries**. This funnel's decisions supersede
   each other frequently; an entry from last week may already be dead.
3. The route roles table in `AGENTS.md` §5 — it names `/`'s primary CTA in prose.
   If you change that CTA, that sentence goes stale and must be updated too.

---

## Rule 1 — Copy lives in data modules, never in JSX

| Route | Copy source of truth |
|---|---|
| `/` | `frontend/src/components/landing/landingFacts.ts` |
| `/check` | `frontend/src/components/check/checkData.ts` |
| `/checklists` | `frontend/src/components/checklists/checklistsData.ts` |

Never inline a new CTA label or reassurance line into `HeroSection.tsx` /
`StickyCtaBar.tsx`. Export a constant and import it.

Two traps:

- **`CHECK_*` constants are commented `/check` 전용.** If a check CTA now also appears
  on `/`, do not just delete that comment and share the constant. The two entry points
  will want to diverge (`1분 학원 점검` vs `1분 학원 점검 시작하기`). Add a separate
  constant for the new entry point and fix the doc comment on both.
- **`CTA_REASSURANCE` describes the waitlist modal**, not a generic promise —
  `"무료 · 이름·연락처 입력 없음 · 언제든 차단 가능"`. Reusing it under a button that
  navigates to `/check` states something false. Every reassurance line must be true of
  what *that* button actually does, verified against the implementation
  (don't write `1분` unless the flow is).

## Rule 2 — There is no frontend test runner

`frontend/package.json` scripts are `dev`, `build`, `start`, `lint`. No jest, vitest,
or playwright — and a copy change is not the moment to introduce one.

Frontend regressions are asserted from **pytest**, by reading the `.ts` files as text:

- `tests/test_landing_copy.py` — ties `MISA_ACADEMY_COUNT` to `data/academies/*.json`
- `tests/test_mini_check_copy.py` — question ids, answer labels, checklist titles

Extend those files. Before editing checklist data, note the existing assertions:

- `text.count('id: "') == 3` — only the three `Checklist` objects carry `id`.
  `ChecklistItem` is `{ title, prompt }`. **Adding an `id` field to items breaks this.**
- `text.count("title:") >= 3 + 30` — adding items is safe; removing them is not.

When you add a CTA destination or an event, add an assertion for it. A destination
regression (`/check` → `/`) is invisible to `npm run build`.

## Rule 3 — The click-event contract spans six places

Adding one funnel event means editing all of these, in one change:

1. `backend/app/core/constants.py` — `ClickEvent` enum member
2. `frontend/src/lib/types.ts` — `ClickEventType` union
3. the call site (see below)
4. `docs/api.md` — the `POST /events` `event` row **and** its 의미 column
5. `tests/test_engagement_api.py` — the accepted-values list
6. `docs/decision-log.md` — what the event means and why it exists

`click_logs.event` is a plain column, **not a DB enum** — no Alembic migration needed.
`app/schemas/engagement.py` validates against the `ClickEvent` enum, so step 1 is what
makes a value legal; an unknown value returns 422.

**Page views are never events.** Only explicit user actions.

### Existing names and what they actually mean

| Event | Fires where | Means |
|---|---|---|
| `kakao_channel` | `KakaoChannelLink` default | organic Kakao channel-add click |
| `checklist_kakao_clicked` | `KakaoChannelLink event=` prop on `/check` result | checklist-reward Kakao click |
| `mini_check_started` | `/check` intro button (`startCheck`) | user began the 3 questions |
| `mini_check_completed` | last question answered | finished all 3 |
| `mini_check_result_viewed` | result phase mount | saw the result |
| `mini_check_home_clicked` | **`/check` result → `/`** (`학원콕 더 알아보기`) | check → home |

⚠️ **`mini_check_home_clicked` is check → home, not home → check.** The name reads
backwards. A home→`/check` CTA needs its own new name (e.g. `home_check_clicked`);
reusing this one merges two opposite funnel directions into a single counter and
destroys both numbers retroactively.

⚠️ **Navigating to `/check` is not `mini_check_started`.** That event is the intro
button only — it is the denominator for check completion rate.

⚠️ **Never call `trackEvent` directly for a Kakao link.** `KakaoChannelLink` holds a
`trackedRef` dedupe guard; bypassing it double-counts. Pass its `event` prop instead.

Tracking must never block the user: every call site is
`trackEvent({...}).catch(() => {})`. Keep that shape.

## Rule 4 — Accessibility invariants

**`StickyCtaBar` has four state expressions that must stay in sync.** With
`shown = visible && !suppressed`:

```
inert={!shown}   aria-hidden={!shown}   tabIndex={shown ? undefined : -1}
className={... shown ? "translate-y-0" : "pointer-events-none translate-y-full"}
```

`suppressed` is `waitlistOpen` from `LandingPage` — the bar hides while the modal is
open so it cannot be tabbed to behind the overlay. If you convert the `<Button>` to a
`next/link`, **`tabIndex={-1}` is still required** — an anchor is natively focusable and
`inert` support cannot be assumed alone.

**`ctaSentinelRef` must stay immediately after the Hero's primary CTA block.** The
sticky bar reveals on `!entry.isIntersecting && boundingClientRect.top < 0` — i.e. the
user scrolled *past* the CTA. Moving the sentinel silently changes when the bar appears.

**Navigation uses a real `href`**, not `onClick` + `router.push`. Middle-click,
open-in-new-tab, and prefetch all depend on it.

The component for this already exists: **`ButtonLink`** from `@/components/ui` — a
`next/link` carrying `buttonClassName()`, so a link-CTA looks identical to a `Button`
with no new styles and no `<button>` nested in an `<a>`. `MiniAcademyCheck.tsx:142`
is the reference usage. Do not hand-roll a styled `<Link>`, and do not add an
`as`/`asChild` prop to `Button`.

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
- keep `stable` results neutral (`"다음 상담에서 확인해 보세요"`), not a hidden problem report
- keep `/check` answers in the browser. No server storage, no login, no contact capture
- `classifyResult` splits *areas needing confirmation*, never academy quality —
  the `개선이 필요해요` / `잘 모르겠어요` / `가끔 아쉬워요` thresholds are decision-log
  settled. Propose changes in the report; don't implement them unasked.
- any number in copy must trace to `data/academies/*.json`. Unverified → `null`, never
  a heuristic.

Note: `CheckQuestion.counseling` is `Partial<Record<Exclude<AnswerId, "well">, string>>`
— there is deliberately no question for a `잘 되고 있어요` answer. If a task asks for
counseling questions on an all-`well` result, that widens the type; flag it rather than
quietly adding a `well` key.

## Rule 6 — Decision-log supersede protocol

Add a **new** `## YYYY-MM-DD — 제목` block at the **top** of `docs/decision-log.md`.
Never edit or delete an older entry — the log's value is showing what was believed when.

State explicitly:

- **계기** — what changed to justify reopening a settled decision
- **결정** — the new rule
- **무엇을 대체하는가** — name the superseded entry by its date and title
- **경로** — the route → role table after the change
- **계측** — which event measures the new conversion
- **바꾸지 않은 것** — the scope you deliberately left alone

Then propagate: `docs/api.md` if events changed, `AGENTS.md` §5 if route roles changed.

---

## Auditing the page (companion skill, scoped)

`landing-page-conversion-audit` is installed for reviewing layout, hierarchy, and copy.
It is an **e-commerce checkout-funnel** skill, so use only part of it:

- **Apply** §A message match (does `/`'s headline repeat the ad's promise in the ad's
  own words), §B above-the-fold on 390×844 (**count the competing CTAs** — this funnel
  runs one primary + one secondary by design), §C offer clarity in 5 seconds,
  §G is a conversion event firing at all.
- **Skip** §D forms, §E payment trust, §F upsells. This product has no checkout, no
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

1. Read `AGENTS.md` §5/§7 and the top 3 `decision-log.md` entries. Name the entry this
   change supersedes, if any.
2. Read the touched components **and** their copy modules before editing.
3. Grep the event names involved across `.py`, `.ts`, `.tsx`, `.md` — confirm each
   name's real meaning at its call site, not from the name.
4. Make copy changes in the data module; components import.
5. Wire destinations with `next/link`; keep sentinel position and sticky-bar a11y props.
6. If an event is new, do all six contract edits together.
7. Extend `tests/test_landing_copy.py` / `test_mini_check_copy.py` for the new
   destination, label, and questions.
8. Write the decision-log entry; propagate to `api.md` / `AGENTS.md`.
9. Validate (below). Report honestly what ran and what didn't.

## Validation

```bash
cd frontend && npm ci && npm run build
cd backend && uv sync && uv run pytest ../tests
```

Both must run. `npm run build` catches TypeScript and route errors but **cannot** catch
a wrong CTA destination or a mislabelled event — that is what the pytest copy tests are
for, which is why step 7 is not optional.

**Behaviour the copy tests still cannot see** — the sticky bar actually hiding while the
modal is open, focus not landing behind the overlay, the CTA really navigating to
`/check` — use the **`webapp-testing`** skill (installed in this repo) to drive
`npm run dev` with an ad-hoc Playwright script. Run it whenever a change touches the
sticky-bar `shown` state, the sentinel, or a CTA destination. Those scripts are
throwaway verification: never add Playwright to `frontend/package.json`.

If `npm ci` fails on a lockfile mismatch: report the failing command, the error summary,
and whether you verified another way. Do **not** bulk-update dependencies to get green.
Leave no build artifacts behind.

Do not deploy, push, or commit unless explicitly asked.

## Common failure modes

| Symptom | Cause |
|---|---|
| Two funnel directions in one counter | reused `mini_check_home_clicked` for home→check |
| `422` on a new event | added to `types.ts` but not to `ClickEvent` enum |
| Sticky button tabbable while modal is open | converted Button→Link, dropped `tabIndex={-1}` |
| Sticky bar appears at the wrong scroll point | sentinel moved away from the CTA |
| Reassurance line promises something false | reused `CTA_REASSURANCE` under a new destination |
| `test_mini_check_copy` fails after adding checklist items | added an `id` field to `ChecklistItem` |
| `test_landing_copy` fails | `MISA_ACADEMY_COUNT` no longer matches `data/academies/*.json` |
| Reviewer asks "what happened to the old decision?" | edited an old decision-log entry instead of superseding it |
