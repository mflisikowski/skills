---
name: lighthouse-check
description: Audit a deployed website with HTTP preflight and Lighthouse, then save a Markdown report with evidence and recommendations. Use for compression checks, mobile or desktop performance audits, deployment acceptance, and reviewing existing Lighthouse reports.
---

# Lighthouse Check

Run the audit yourself and deliver a Markdown file. The user supplies the URL and
goal; discover commands, prepare tools and collect evidence as the agent. Keep HTTP
observations, browser validation and Lighthouse measurements distinct.

## 1. Choose and execute the request

Use the requested URL. If it is missing, inspect project deployment documentation
and ask only if the target remains ambiguous. Use the user's language in the report.
The bundled renderers support `en` and `pl`; for another language, translate the
Markdown while retaining measurements and links to the source evidence.

Resolve paths relative to this skill. For a full audit, run the [audit command](scripts/audit.py):

```sh
python3 <skill-dir>/scripts/audit.py https://example.com/ --language pl
```

It performs preflight, checks an anonymous browser navigation and runs Lighthouse
three times sequentially in fresh profiles. It writes `report.md`, `audit.json`,
preflight evidence, browser evidence and each Lighthouse JSON under a unique
directory in `.scratch/lighthouse-check/artifacts/`. Read `--help` for limits,
desktop mode, number of runs, existing tools and output options. Choose a fresh
output directory when overriding the default.

For transport checks only, add `--preflight-only`. To review existing exports,
use one or more `--report <file.json-or-html>` arguments instead of a URL. Report
review is offline: identify the source timestamps and state that the current
deployment was not checked. JSON embedded in HTML is parsed without executing scripts.

Before using software behavior or choosing flags, inspect pinned versions through
OpenSRC; fall back to installed source and official documentation if unavailable,
and state remaining uncertainty. The executor prefers installed project tools.
If absent, it prepares the [pinned tool manifest](assets/tools-package.json) in an
isolated audit directory, retaining the resolved lockfile. It does not change
application dependencies. Use `--no-install` when preparation is not authorized,
or `--tools-dir` for an existing package root. Preparation needs network access.

The runtime requires Python 3, curl with compression support, a compatible Node.js
and Chrome/Chromium. Discover available executables and the requested browser.
When a prerequisite is missing, prepare it within the available authorization and
environment permissions, then retry. Supply `--chrome-path` for a particular
Chrome/Chromium executable. If preparation is unavailable, deliver the generated
incomplete report with the exact reason and required next step.

## 2. Interpret HTTP evidence

The standalone [transport helper](scripts/preflight.py) remains available:

```sh
python3 <skill-dir>/scripts/preflight.py https://example.com/ \
  --output .scratch/lighthouse-check/artifacts/preflight.json --language pl
```

It discovers same-origin scripts, modulepreloads and stylesheets in the returned
HTML, and checks HTML plus those assets. `--include-external` includes discovered
cross-origin startup assets in the same limits; the full audit enables it. Add
`--asset URL` yourself for known dynamic chunks, API responses or CDN assets.
Discovery does not crawl routes, CSS dependencies, images or fonts, or execute JS.
Skipped required assets and truncated discovery prevent complete coverage. A
`PASS` applies only to the recorded, bounded scope. The standalone helper writes
JSON and a sibling Markdown file for each completed request, including failures.

It requests compression supported by the installed curl and compares static
asset responses against `Accept-Encoding: identity`. curl decodes the response,
while `size_download` records transferred body bytes. Reports retain selected
diagnostic headers, not cookies or full response bodies.

| Verdict / exit | Action |
| --- | --- |
| `PASS` / 0 | Transport passed for the listed URLs. Continue with browser checks. |
| `BLOCKED` / 1 | Record the transport issue; distinguish diagnostic measurement from deployment acceptance. |
| `INCONCLUSIVE` / 2 | Restore access or complete coverage. Failed connections do not establish absent compression. |

Important distinctions:

- `Content-Encoding`, successfully decoded content and measured bytes establish
  compression. `Vary`, `.min.js`, hashed names and local gzip sizes alone do not.
- Brotli, gzip, deflate and zstd are valid when negotiated and decoded by curl.
  State codec coverage limits: a gzip-only probe does not disprove Chrome Brotli support.
- Text below the helper's size threshold is exempt. Already compressed images,
  fonts and video do not need HTTP gzip to pass.
- Minification warnings are hints for source/build inspection. Line lengths and
  size ratios cannot prove minification. Development entrypoints block acceptance.
- Missing `Vary: Accept-Encoding` on compressed content is a cache warning.
  Resolve or explain it before calling the deployment ready.

Interpret recorded cache directives in content context: versioned files, HTML and
personalized responses need different policies. Missing `Cache-Control` does not
prove caching is disabled. This helper does not test cache revalidation. curl
timings describe the client request, not isolated server processing or Lighthouse.

For a diagnostic audit, retain transport failures and continue if the intended
page can be confirmed. Missing compression alone does not prevent a baseline.
For deployment acceptance, unresolved material transport failures block a positive
verdict even when Lighthouse completed. Unavailable or substituted target content
requires an incomplete report. Report the exact URL, observed evidence and next
action. Server changes and deployment require their own authorization.

## 3. Confirm the browser scenario

Inspect the executor's browser metadata and screenshot. It records visible content,
console errors, visible images, viewport, anonymous consent state and obvious access
or login screens. Use `--expected-text` when a stable content marker identifies
the target. These checks are evidence, not a general semantic proof that an app
works. Confirm app-specific content and hero/slider images with available browser
tools; restore temporary overrides. Record any browser checks you could not make.

Measure in a clean profile without extensions. Record URL, deployment/commit when
known, time, consent state, viewport, Lighthouse version and throttling. Existing
user tabs are useful for debugging but may not provide a clean baseline. Separate
cold and warm cache runs. Login/error/interstitial pages are not the target app.

The bundled path supports public anonymous navigation. For authenticated or
interactive scenarios, inspect the project's existing workflow and preserve its
state deliberately; otherwise report the unsupported scenario and missing access.
Login, error and interstitial screens must not become a successful target-page audit.

## 4. Explain the measurements

Read every generated artifact before declaring success. The [measurement driver](scripts/measure.mjs)
uses temporary Chrome profiles and closes only browsers it owns. Keep all attempts,
including failures. The full audit exits 0 for completed work, including transport
findings, and 2 for incomplete work; its process result does not establish deployment quality.

Compare matching URLs, versions and settings; retain medians and ranges of valid
runs. Mismatched reports are listed individually rather than combined. Matching
metadata does not establish identical hardware or network conditions. Bytes saved
do not predict a new Lighthouse score. Additional runs are appropriate when the
observed variability makes the initial three insufficient.

Report score, FCP, LCP, TBT, CLS, transfer and evidence-backed priorities. Separate
extension URLs from application unused-JS savings. Headers add transfer overhead;
cached transfer can be zero. Keep observed and simulated timings distinct.
Staging `noindex` affects SEO, not Performance; preserve intended test indexing.

Compare Lighthouse's `network-requests` with the preflight URL list. When critical
dynamic JS/CSS or public GET API responses were outside the initial scan, run the
transport helper with those `--asset` URLs and retain a separate supplemental
JSON/Markdown pair. Adjust the bounded asset limit to the observed list if needed.
Identify this as a post-measurement check; an initial `PASS` does not cover these
newly observed resources. Include supplemental failures in the final assessment.

## 5. Deliver the report

Finish the generated `report.md` with a concise assessment in the user's language.
Separate readiness to measure, coverage and deployment quality. State the stage
reached, findings and limitations. Give each material issue an evidence reference,
impact, priority, recommended action and a way to confirm the improvement. Merge
overlapping HTTP and Lighthouse findings so the same defect is not counted twice.
Keep facts separate from suspected causes. Use the JSON details when the generated
finding summary is insufficient; estimated savings are not additive.

Link the Markdown file in your final response. An incomplete audit still produces
a report explaining why; missing measurements have no invented score. Report review
must identify historical timestamps. The shared [report renderer](scripts/reporting.py)
provides the evidence sections; agent interpretation completes the assessment.

For development, use the [HTTP contract tests](scripts/test_preflight.py),
[audit command tests](scripts/test_audit.py) and [real-browser test](scripts/test_live.py).
The last is opt-in via `LIGHTHOUSE_TEST_TOOLS` pointing to an installed package root.
Run the repository validator when changing bundled helpers:

```sh
python3 scripts/check.py
```

Distributed under the [MIT license](LICENSE). Keep this license with copied skill files.
