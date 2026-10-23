---
name: lighthouse-check
description: Verify deployed HTTP compression and browser readiness before running Lighthouse, or compare Lighthouse reports with their test conditions. Use for mobile performance checks, gzip/Brotli verification, and deployment performance acceptance.
---

# Lighthouse Check

Check the deployed URL, then decide whether a Lighthouse comparison would be
meaningful. Keep transport checks separate from minification and browser rendering.
The helper makes read-only GET requests; it does not deploy, modify servers,
install Lighthouse, or launch an audit.

## 1. Check transport

Use the user's URL. With no URL, inspect project deployment docs and ask only if
the intended environment remains ambiguous. Consult OpenSRC for installed tool
versions before changing helper behavior or choosing Lighthouse flags. If OpenSRC
is unavailable, inspect the pinned versions and current official documentation;
state any unresolved version uncertainty.

Run the [bundled helper](scripts/preflight.py), resolving its path relative to this skill:

```sh
python3 <skill-dir>/scripts/preflight.py https://example.com/ \
  --output .scratch/lighthouse-check/preflight.json
```

It discovers same-origin scripts, modulepreloads and stylesheets in the returned
HTML, and checks HTML plus those assets. Add `--asset URL` for known dynamic
chunks, API responses or CDN assets. Discovery is bounded and does not crawl
routes or execute JavaScript. A partial scan cannot pass.

It requests compression supported by the installed curl and compares static
asset responses against `Accept-Encoding: identity`. curl decodes the response,
while `size_download` records transferred body bytes. Reports retain selected
diagnostic headers, not cookies or full response bodies.

| Verdict / exit | Action |
| --- | --- |
| `PASS` / 0 | Transport passed for the listed URLs. Continue with browser checks. |
| `BLOCKED` / 1 | Resolve the HTTP, MIME, compression or representation problem before performance acceptance. |
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

On `BLOCKED` or `INCONCLUSIVE`, stop the default audit flow and give the exact
URL, encoding, MIME, downloaded/decoded bytes, command and next owner. Compare
container and public proxy responses with available authorized access. If the
user explicitly requests a diagnostic baseline despite failure, label it as such
and retain failed preflight evidence beside the report.

## 2. Check the browser

Use the browser requested by the user. Check fresh navigation, console errors,
app error screens and loaded hero/slider images. Confirm the intended mobile
viewport and restore temporary overrides. A successful build/HTTP check does
not establish SPA rendering: image transforms can be absent while a build succeeds.

Measure in a clean profile without extensions. Record URL, deployment/commit when
known, time, consent state, viewport, Lighthouse version and throttling. Existing
user tabs are useful for debugging but may not provide a clean baseline. Separate
cold and warm cache runs. Login/error/interstitial pages are not the target app.

Proceed to acceptance only after transport and browser checks pass, with material
warnings resolved or documented. Prefer the project's installed Lighthouse workflow.
Installation and deployment changes are outside this skill's implied scope.

## 3. Measure or review Lighthouse

Compare matching settings and the median of 3–5 runs. Retain JSON reports and
preflight evidence together. Bytes saved do not predict a new Lighthouse score.

Analyze user-supplied reports even if live preflight is unavailable; state that
limitation. Read JSON directly. For HTML exports, parse `window.__LIGHTHOUSE_JSON__`
as JSON without executing embedded scripts.

Report score, FCP, LCP, TBT, CLS, transfer and evidence-backed priorities. Separate
extension URLs from application unused-JS savings. Headers add transfer overhead;
cached transfer can be zero. Keep observed and simulated timings distinct.
Staging `noindex` affects SEO, not Performance; preserve intended test indexing.

## Output

Lead with `READY FOR LIGHTHOUSE`, `FIX BEFORE LIGHTHOUSE`, or `ACCESS/COVERAGE
INCOMPLETE`. Include the stage reached, a compact evidence table, warnings,
artifact paths and the next concrete check. Report-only reviews must identify
the report timestamp rather than claiming it describes the current deployment.

Validate the helper with the [contract tests](scripts/test_preflight.py):

```sh
python3 <skill-dir>/scripts/test_preflight.py
```

Distributed under the [MIT license](LICENSE). Keep this license with copied skill files.
