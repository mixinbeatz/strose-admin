# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The staff admin portal for Saint Rose Philippine Duchesne parish (companion to the "Saint Rose Anthem" parish app/website). It is a **static, single-page site with no build step**: `index.html` is one ~6,600-line file containing all CSS, markup, and JavaScript for the entire app. There is no `package.json`, bundler, framework, or test suite — it's deployed as-is via GitHub Pages (see `CNAME`: `portal.saintroseanthem.org`).

This repo is one piece of a wider "Saint Rose Anthem" web presence that shares the same Firebase project and design system across sibling repos — notably the public site at `saintroseanthem.org` (public-facing pages like a parish-registration form or advertise/partner-request form, not part of this repo). Facts below about the Firestore path convention and design system apply across that whole family, not just this repo.

**Deploy**: pushing to `main` on GitHub deploys live immediately via GitHub Pages — there is no build, staging, or release step in between. **Git workflow is trunk-based**: commit directly to `main`, no feature branches, no PRs/merge commits.

- `index.html` — the whole portal app (login screen + sidebar SPA with client-side page routing).
- `finance.html` — a separate, smaller standalone page (Sacred Apps Finance Portal), same visual style, own `<script>`.
- `images/`, `images extras/` — static assets (favicons, hero photos).
- `splice_*.py` — one-off Python scripts used in the past to make large, precise multi-point edits to `index.html` (see "Making large edits" below). Not a build tool, not run automatically.

There is no backend code in this repo. All data and auth live in a Firebase project (`saint-rose-anthem`) that this static frontend talks to directly over REST.

## Running / testing locally

No install or build step. Just open the file or serve it statically, e.g.:

```bash
python3 -m http.server 8000   # then visit http://localhost:8000/index.html
```

There are no automated tests or linters configured in this repo. Verify changes by opening the page in a browser and clicking through the relevant flow (login with a real staff/ministry account against the live Firebase project, since there's no local backend/mocking).

## Architecture (index.html)

**Everything lives in three parts of one file:** a big `<style>` block (CSS custom properties for the burgundy/gold parish theme), the HTML body (`#login-screen`, then `#app` = `.sidebar` nav + `.main .content` holding one `<div class="page" id="page-...">` per screen, all but the active one hidden via CSS), and one `<script>` block with all logic — no modules, no imports.

**Backend is Firebase, called directly from the browser with a hardcoded API key** (this is normal for Firebase's client SDK-style usage; access control is enforced by Firestore security rules + custom claims server-side, not by hiding the key):
- **Auth**: Firebase Identity Toolkit REST endpoints (`identitytoolkit.googleapis.com`) for sign-in, password reset, and refresh-token exchange. The ID token is a JWT decoded client-side (`decodeJwt`) to read custom claims (`role`, `ministry`, `email`) — there is no separate user/role table in the UI, the JWT claims *are* the permission model. Session (`authIdToken` / `authRefreshToken`) lives in `localStorage`; `getValidIdToken()` transparently refreshes an expiring token before each authed call.
- **Data**: Cloud Firestore accessed via its plain REST API (`BASE = firestore.googleapis.com/.../parishes/saint-rose-anthem`), not the Firestore SDK. All reads/writes go through a handful of small helpers — `fs_get`, `fs_get_doc`, `fs_post`, `fs_patch`, `fs_delete` — which wrap `fetch` and attach the ID token via `authHeaders()`. Firestore's REST JSON shape (`{fields: {key: {stringValue: ...}}}`) is used directly; `gf(doc, key)` reads a typed field back out, `docId(doc)` extracts the doc id from its resource name. New Firestore-backed features should follow this same `fs_*` + `gf`/`docId` pattern rather than introducing a new data-access style.
- **File uploads**: images are read client-side as base64 (`FileReader.readAsDataURL`), optionally resized/compressed in-canvas (`compressImageIfNeeded`, `resizeImageTo`, `uploadDevFileDual` for a web + app-sized pair), then PUT to Firebase Storage's REST upload endpoint (`firebasestorage.googleapis.com/.../uploadType=media`) with the same API key.
- **Privileged server-side ops** (granting roles, listing staff accounts) go through Cloud Functions (`FUNCTIONS_BASE = us-central1-saint-rose-anthem.cloudfunctions.net/<functionName>`), not Firestore directly — Firestore security rules don't allow clients to self-assign roles.

**Role-based navigation, not route-based**: there's no router. `showPage(id, el)` toggles `.page.active` / `.nav-item.active` and calls that page's `load*()` function to (re)fetch its data on demand — pages don't auto-refresh in the background. Which sidebar sections/items are visible is entirely CSS-class + `applyRoleNav()` driven: elements are tagged `staff-only`, `cheyanne-only`, `ministry-only`, `ministry-leader` (optionally scoped further via `data-ministry="mens"` etc.), or `owner-admin-only`, and `applyRoleNav()` derives booleans from the JWT claims (`currentClaims.role`, `currentClaims.ministry`, and a special-cased email for Cheyanne) to show/hide each tagged element and to auto-land the user on their default page after login. When adding a new staff-only or ministry-scoped page, add the matching class(es)/`data-ministry` to its nav item rather than writing new gating logic.

**Ministries are data-driven, not hardcoded**: the `ministries` Firestore collection is the live registry (`loadMinistryRegistry()` populates `ministryRegistry`/`MINISTRY_NAME_MAP` and the "All Ministries" nav group at runtime). `MINISTRY_NAME_DEFAULTS` is only a fallback shown briefly before that fetch resolves. A ministry only gets a bespoke dedicated page (like Men's Ministry) if its id is added to `MINISTRIES_WITH_DEDICATED_PAGES`; otherwise ministry leaders fall back to the generic `.ministry-only` pages (My Ministry / Post to Members / My Members / Submit Event / etc.) — this is the safe default while onboarding a new leader before a custom page exists.

**Staff identity**: `STAFF_NAME_MAP` maps known staff emails to display names for the sidebar greeting; it's a display convenience only, not part of the permission model (that's the JWT claims).

## CRITICAL: Firestore path convention

Every Firestore read/write — in this repo and any sibling repo touching this data — must use the nested per-parish path `parishes/saint-rose-anthem/{collection}`, exactly what `BASE` already resolves to here. **Never** write to a root-level collection path (`{collection}` with no `parishes/saint-rose-anthem/` prefix). Firestore security rules only permit the nested path; a root-level write is silently rejected (or, if rules ever momentarily allowed it, orphaned from everything else that reads the nested path).

This already bit the project once for real: `advertise.html` (sibling public-site repo) posted partner/advertising submissions to a dead root-level path, and real form submissions were silently lost for weeks before anyone noticed — the write appeared to succeed client-side but the rules rejected it. When adding or reviewing *any* code that writes to Firestore (in this repo or elsewhere in the project), explicitly check the path is nested under `parishes/saint-rose-anthem/` before considering the work done — don't assume a copy-pasted snippet got it right.

## Public forms writing without login

Some Firestore collections (e.g. `familyRegistrations`, form submissions from the public site) are written by unauthenticated public forms — that's intentional, not a bug, and it's why not every write in this codebase goes through `authHeaders()`. It's allowed only because the corresponding Firestore security rule explicitly grants an `isPublicSubmission`-style unauthenticated-create rule scoped to that one collection/shape. Never assume a collection is publicly writable by default — if you add a new public-facing form (in this repo or a sibling one), it needs its own explicit rule following that same pattern, not an open collection.

## Design system: "Sonoran Dusk"

The same palette and type pair is used across this portal, `finance.html`, and the public site — implemented as CSS custom properties on `:root` (names vary slightly by file; `finance.html` only defines the subset it uses):

| Token | Hex | CSS var here |
|---|---|---|
| Burgundy | `#5C1A2E` | `--burgundy` |
| Dusty Rose | `#C17A8A` | `--dusty-rose` |
| Gold | `#C9A84C` | `--gold` |
| Linen | `#E8DDD0` | `--linen` |
| Sand | `#F7F3EE` | `--sand` |
| Soil | `#3D2B2B` | `--soil` |

`index.html` additionally defines `--burgundy-dark`, `--burgundy-light`, `--gold-light`, `--white`, `--success`, `--danger` for states/variants not in the base palette. Headers/titles use `'Cinzel', serif` (loaded from Google Fonts), body text uses `'Faustina', serif`. Match these existing var names when styling anything new rather than hardcoding hex values or inventing new tokens.

## Making large edits to index.html

Because this is a single very large HTML file, prefer targeted `Edit` calls with enough surrounding context to be unique, the same way the `splice_*.py` scripts in this repo did it historically: locate the exact old block, replace it with the new block, and if a script-style approach is easier for a many-point mechanical change, a short Python script asserting `content.count(old) == 1` before replacing (as those scripts do) is a reasonable pattern to reuse — but it's not required tooling, just a precedent you'll see in git history.

When editing the JS in `<script>`, keep with the existing style: inline `onclick="..."` handlers on markup (not addEventListener-based wiring, except a few keydown listeners), template-literal HTML strings built up and assigned via `innerHTML` for dynamic lists, and `showToast(message, 'success'|'error')` for user feedback after an action rather than inline error text (login form is the one exception, using dedicated error `div`s).
