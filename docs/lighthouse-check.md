# Use lighthouse-check

`lighthouse-check` audits a deployed page and produces a Markdown report with supporting evidence. Use it to investigate performance, check HTTP compression, assess a deployment, or review saved Lighthouse results.

Start with the [installation instructions](../README.md#install-a-skill). The installed [SKILL.md](../skills/lighthouse-check/SKILL.md) tells the agent how to collect evidence and complete the assessment.

## Choose a mode

| Goal | Ask the agent | Work performed |
| --- | --- | --- |
| Audit a public page | `Use $lighthouse-check to audit https://example.com/ on mobile and save the report in Polish.` | HTTP preflight, anonymous browser navigation, and three sequential Lighthouse runs by default. |
| Check transport only | `Use $lighthouse-check to check HTTP compression on https://example.com/ without running Lighthouse.` | HTTP checks and a report, without Chrome or Lighthouse. |
| Review saved results | `Use $lighthouse-check to review ./before.json and ./after.html.` | Offline analysis of the supplied exports, including their original timestamps and comparability. |

For deployment acceptance, say that this is the goal. Unresolved material HTTP findings block a positive acceptance assessment even when Lighthouse measurements complete. A diagnostic audit can retain those findings and still measure the intended page.

The bundled browser flow supports public anonymous navigation. Authenticated or interactive scenarios need explicit handling by the agent using the consuming project's tools and access. A login, error, or interstitial page must not count as the intended application.

## Requirements

| Mode | Tools |
| --- | --- |
| HTTP checks | Python 3 and curl 7.70 or later with compression support. |
| Full audit | HTTP tools, Node.js 22.19 or later, compatible Lighthouse tools, and Chrome/Chromium. npm and network access are needed for automatic tool preparation. |
| Saved-report review | Python 3 and readable Lighthouse JSON or HTML exports. No browser or live deployment access is needed. |

The skills installer separately requires Node.js 22.20 or later. Development and CI use the Python version in [.python-version](../.python-version).

The executor tries Lighthouse installed in the working project or its parent directories, then its audit tool cache. If none works, it installs the [bundled manifest](../skills/lighthouse-check/assets/tools-package.json) under `.scratch/lighthouse-check/artifacts/tools/`. It preserves a copy of the resolved lockfile with the audit and leaves application dependencies untouched.

Use `--tools-dir` to select an existing package root or `--no-install` to require tools already available. An explicit tools directory that fails validation produces an incomplete audit; it does not trigger an automatic installation elsewhere. Tool preparation and browser execution must fit the environment's permissions.

## Run the helpers directly

These examples run from this repository's root. In a consuming project, replace `skills/lighthouse-check` with the installed skill directory. Output paths are relative to the working directory where you run the command.

### Audit a page

```sh
python3 skills/lighthouse-check/scripts/audit.py https://example.com/ --language pl
```

This performs HTTP preflight, confirms an anonymous browser scenario, and runs Lighthouse three times on mobile using fresh browser profiles. For desktop or a stable content marker:

```sh
python3 skills/lighthouse-check/scripts/audit.py https://example.com/ \
  --device desktop --expected-text "Example Domain" --language en
```

The executor records browser metadata and a screenshot. The agent still needs to inspect that evidence and confirm application-specific content before declaring success.

### Run HTTP checks alone

Use the audit wrapper to produce the same report layout without measurements:

```sh
python3 skills/lighthouse-check/scripts/audit.py https://example.com/ \
  --preflight-only --language pl
```

For transport-specific options and a verdict-based exit code, use the standalone helper:

```sh
python3 skills/lighthouse-check/scripts/preflight.py https://example.com/ \
  --include-external \
  --asset https://example.com/assets/dynamic.js \
  --output .scratch/lighthouse-check/artifacts/manual/preflight.json
```

Replace the extra asset URL with a real resource you need to check, or omit `--asset`. The standalone helper writes JSON and a sibling Markdown report. Choose a new output path for each check to preserve earlier evidence.

### Review existing reports

```sh
python3 skills/lighthouse-check/scripts/audit.py \
  --report ./before.json --report ./after.html --language en
```

Supply either a URL or one or more `--report` files. Review mode extracts saved Lighthouse data without executing scripts embedded in HTML. It does not check the current deployment. Reports with mismatched URLs, versions, or settings are listed individually rather than aggregated.

### Adjust an audit

| Option | Use |
| --- | --- |
| `--output-dir PATH` | Select a new or empty directory. The audit wrapper rejects a nonempty destination. |
| `--language en` or `--language pl` | Choose the bundled report language; the default is English. Ask the agent to translate for other languages. |
| `--runs N` | Set 1–10 Lighthouse runs; the default is 3. |
| `--device mobile` or `--device desktop` | Choose the measurement profile; the default is mobile. |
| `--expected-text TEXT` | Require a stable text marker on the intended page. |
| `--asset URL` | Add a known dynamic chunk, CDN resource, or public GET API response. Repeat for multiple URLs. |
| `--max-assets N` | Adjust the bounded asset count; the default is 24. |
| `--timeout N` | Set the per-request HTTP timeout in seconds; the default is 15. |
| `--tools-dir PATH` | Use a package root containing installed Lighthouse tools. |
| `--no-install` | Use available tools without automatic preparation. |
| `--chrome-path PATH` | Select a Chrome/Chromium executable. |

Read the helpers' current options with:

```sh
python3 skills/lighthouse-check/scripts/audit.py --help
python3 skills/lighthouse-check/scripts/preflight.py --help
```

## Read the output

The audit wrapper prints the path to `report.md`. Its default destination is a unique timestamped directory under `.scratch/lighthouse-check/artifacts/`.

| Artifact | Contents |
| --- | --- |
| `report.md` | Generated evidence sections; the agent completes the assessment and recommended actions. |
| `audit.json` | Execution status, errors, HTTP evidence, run records, and comparison summary. |
| `preflight.json` | HTTP evidence when preflight ran. |
| `browser.png` | Screenshot when browser capture succeeded. |
| `lighthouse-*.json` | Individual Lighthouse results, including retained failed attempts where available. Review mode also copies the supplied data into this format. |
| `request.json`, `measurement.json`, `runner.log` | Measurement settings, execution metadata, and diagnostic output when that stage ran. |
| `install.log`, `tools-lock.json` | Tool preparation log and resolved dependency lockfile when available. |

An incomplete audit can have fewer artifacts. Follow the links in `report.md` to see what was actually collected. Preserve the directory when sharing the report so its relative evidence links work.

### Execution status and exit codes

`audit.py` reports whether the requested work completed:

| Status | Exit code | Meaning |
| --- | --- | --- |
| `COMPLETED` | 0 | Browser validation and the requested measurements completed. Read the findings to assess quality. |
| `PREFLIGHT_ONLY` | 0 | HTTP-only work completed. The HTTP verdict can still be `BLOCKED` or `INCONCLUSIVE`. |
| `REPORT_REVIEW` | 0 | Saved reports were processed. The current deployment was not checked. |
| `INCOMPLETE` | 2 | A prerequisite, access, scenario, or execution problem prevented completion. Read the recorded reason. |

Argument errors also exit with code 2 and may occur before any report is created. A zero exit code is not a deployment acceptance verdict.

The standalone `preflight.py` instead maps its HTTP verdict to the process result:

| Verdict | Exit code | Meaning |
| --- | --- | --- |
| `PASS` | 0 | Transport passed within the recorded scope. |
| `BLOCKED` | 1 | Transport findings require attention. |
| `INCONCLUSIVE` | 2 | Access or coverage is insufficient for a conclusion. |

### Coverage and interpretation

Preflight checks the HTML and startup scripts, module preloads, and stylesheets discovered in it. The audit wrapper includes discovered cross-origin assets; the standalone helper requires `--include-external` for those. Discovery does not execute JavaScript, crawl other routes or CSS dependencies, or enumerate images and fonts. Add known resources with `--asset`; skipped required assets or truncated discovery prevent complete coverage.

After measurement, the agent compares Lighthouse's network requests with the preflight list and checks critical missing resources separately. A `PASS` applies to the recorded URLs and limits, not every resource the application might request.

Compression findings combine response headers, decoded content, and transferred body bytes. Failed connections do not establish missing compression. Cache headers and minification hints need interpretation in the application's context.

Compare measurements only when their URLs, Lighthouse versions, and settings match. The report retains medians and ranges for comparable valid runs. Matching metadata alone does not establish identical hardware or network conditions, and estimated byte savings do not predict a new Lighthouse score.

## Resolve an incomplete audit

| Observation | Next step |
| --- | --- |
| Node.js or Lighthouse tools are unavailable | Provide a compatible Node.js, allow isolated preparation, or select a working `--tools-dir`. |
| Chrome is unavailable or cannot launch | Supply `--chrome-path` or resolve browser execution permissions. |
| The target returns a login, error, or unexpected page | Restore access and confirm the intended scenario. Use a content marker with `--expected-text` where appropriate. |
| HTTP requests fail or asset discovery is truncated | Restore access or adjust the scope and limits, then rerun. Keep the earlier evidence. |
| Measurement stops partway through | Read `runner.log`, `measurement.json`, and the report's errors; rerun into a fresh output directory after resolving the cause. |
| Existing exports cannot be combined | Check the source URLs, timestamps, versions, and settings. Interpret each result separately when conditions differ. |

The agent should deliver the report even when execution is incomplete, stating the stage reached, the reason, and the next action. Server changes and deployment are separate work requiring their own authorization.

For changes to the skill itself, see [Contributing](../CONTRIBUTING.md).
