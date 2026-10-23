#!/usr/bin/env python3
"""Run HTTP preflight and Lighthouse, preserving JSON evidence and a Markdown report."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from preflight import check, web_url
from reporting import lighthouse_markdown, link, preflight_markdown, run_record, summarize, text


SCRIPTS = Path(__file__).resolve().parent


def tools_for(args, output):
    node = shutil.which('node')
    if not node:
        raise ValueError('Node.js is unavailable; the agent must provide Node.js before measuring')
    version = subprocess.run([node, '--version'], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    if tuple(int(part) for part in version.lstrip('v').split('.')[:2]) < (22, 19):
        raise ValueError(f'Node.js {version} is unsupported; the bundled tools require >=22.19')
    candidates = [args.tools_dir.resolve()] if args.tools_dir else [
        parent for parent in [Path.cwd(), *Path.cwd().parents]
        if (parent / 'node_modules/lighthouse/package.json').is_file()]
    cache = Path('.scratch/lighthouse-check/artifacts/tools').resolve()
    if not args.tools_dir:
        candidates.append(cache)
    for folder in candidates:
        result = subprocess.run([node, str(SCRIPTS / 'measure.mjs'), '--check-tools', str(folder)],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return node, folder, json.loads(result.stdout)
    if args.tools_dir or args.no_install:
        raise ValueError('Lighthouse tools are unavailable; provide a working --tools-dir or allow isolated preparation')
    npm = shutil.which('npm')
    if not npm:
        raise ValueError('npm is unavailable for isolated Lighthouse preparation')
    cache.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPTS.parent / 'assets/tools-package.json', cache / 'package.json')
    with (output / 'install.log').open('w') as log:
        subprocess.run([npm, 'install', '--prefix', str(cache), '--ignore-scripts', '--no-audit', '--no-fund',
                        '--fetch-retries=0', '--fetch-timeout=30000'], stdout=log, stderr=log,
                       check=True, timeout=180)
    result = subprocess.run([node, str(SCRIPTS / 'measure.mjs'), '--check-tools', str(cache)],
                            capture_output=True, text=True, check=True, timeout=30)
    return node, cache, json.loads(result.stdout)


def measure(url, args, output, report):
    node, folder, info = tools_for(args, output)
    report['tools'] = {**info, 'directory': str(folder)}
    lock = folder / 'package-lock.json'
    if lock.is_file():
        shutil.copyfile(lock, output / 'tools-lock.json')
    request = {'url': url, 'output_dir': str(output.resolve()), 'tools_dir': str(folder),
               'runs': args.runs, 'device': args.device, 'language': args.language,
               'expected_text': args.expected_text, 'chrome_path': args.chrome_path}
    (output / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
    with (output / 'runner.log').open('w') as log:
        process = subprocess.Popen([node, str(SCRIPTS / 'measure.mjs'), str((output / 'request.json').resolve())],
                                   stdout=log, stderr=log)
        try:
            process.wait(timeout=args.runs * 150 + 90)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            report['errors'].append('Measurement timed out or was interrupted; partial evidence was retained')
    path = output / 'measurement.json'
    if not path.is_file():
        raise ValueError('Measurement failed before producing metadata; inspect runner.log')
    state = json.loads(path.read_text())
    if process.returncode and not state.get('errors'):
        report['errors'].append(f'Measurement process exited with code {process.returncode}; inspect runner.log')
    report['browser'] = state.get('browser')
    report['tools'].update({key: state[key] for key in ['chrome_version', 'node_version', 'lighthouse_version'] if key in state})
    report['errors'].extend(state.get('errors', []))
    for filename in state.get('files', []):
        record = run_record(json.loads((output / filename).read_text()), filename)
        if filename in state.get('invalid_files', []):
            record['runtime_error'] = {'code': 'SCENARIO_MISMATCH', 'message': 'Measured content did not match the confirmed scenario'}
            record['metrics'], record['scores'] = {}, {}
        report['runs'].append(record)
    if state['status'] == 'COMPLETED' and not report['errors']:
        report['status'] = 'COMPLETED'


def save(report, output, language):
    report['summary'] = summarize(report['runs'])
    (output / 'audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    pl = language == 'pl'
    lines = ['# Audyt strony' if pl else '# Website audit', '',
             f'**Status: {report["status"]}**', '', f'URL: {text(report["url"])}', '',
             f'UTC: {report["started_at"]}', '']
    if report['errors']:
        lines += ['## Przyczyna przerwania' if pl else '## Reason for stopping', '']
        lines += [f'- {text(error)}' for error in report['errors']]
    if report['status'] == 'REPORT_REVIEW':
        lines += ['Analiza historycznych raportów; nie sprawdzono obecnego wdrożenia.' if pl
                  else 'Historical report review; the current deployment was not checked.', '']
    if report.get('tools'):
        tools = report['tools']
        lines += ['## Narzędzia i warunki' if pl else '## Tools and conditions', '',
                  f'- Lighthouse: {text(tools.get("lighthouse_version", "—"))}',
                  f'- Node.js: {text(tools.get("node_version", "—"))}',
                  f'- Chrome: {text(tools.get("chrome_version", "—"))}', '']
    if report.get('browser'):
        browser = report['browser']
        lines += ['## Scenariusz w przeglądarce' if pl else '## Browser scenario', '',
                  f'- URL: {text(browser["final_url"])}',
                  f'- {"Tytuł" if pl else "Title"}: {text(browser["title"])}',
                  f'- {"Nagłówek" if pl else "Heading"}: {text(browser["heading"])}',
                  f'- {"Scenariusz potwierdzony" if pl else "Scenario confirmed"}: {browser["ready"]}',
                  f'- {"Widok" if pl else "Viewport"}: {browser["viewport"]["width"]} × {browser["viewport"]["height"]}',
                  'Świeży profil anonimowy; nie wykonywano interakcji z banerem zgód.' if pl
                  else 'Fresh anonymous profile; no consent-banner interaction.', '', link('browser.png'), '']
        for error in browser.get('console_errors', []):
            lines += [f'- Console: {text(error)}']
        for image in browser.get('broken_visible_images', []):
            lines += [f'- {"Obraz bez załadowanych danych" if pl else "Image without loaded data"}: {text(image)}']
    if report.get('preflight'):
        (output / 'preflight.json').write_text(json.dumps(report['preflight'], indent=2) + '\n')
        lines += ['\n'.join('#' + line if line.startswith('#') else line
                            for line in preflight_markdown(report['preflight'], language).splitlines())]
    lines += [lighthouse_markdown(report, language)]
    lines += ['## Artefakty' if pl else '## Artifacts', '', link('audit.json')]
    if report.get('preflight'):
        lines += [link('preflight.json')]
    for filename in ['request.json', 'measurement.json', 'runner.log', 'install.log', 'tools-lock.json']:
        if (output / filename).is_file():
            lines += [link(filename)]
    (output / 'report.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?')
    parser.add_argument('--report', type=Path, action='append', default=[], help='Review an existing Lighthouse JSON or HTML report')
    parser.add_argument('--preflight-only', action='store_true')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--language', choices=['en', 'pl'], default='en')
    parser.add_argument('--asset', action='append', default=[])
    parser.add_argument('--max-assets', type=int, default=24)
    parser.add_argument('--timeout', type=int, default=15, help='Seconds per HTTP request')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--device', choices=['mobile', 'desktop'], default='mobile')
    parser.add_argument('--tools-dir', type=Path, help='Existing package root containing Lighthouse')
    parser.add_argument('--no-install', action='store_true', help='Use existing tools only')
    parser.add_argument('--chrome-path', help='Requested Chrome/Chromium executable')
    parser.add_argument('--expected-text', help='Required text for the intended anonymous page')
    args = parser.parse_args()
    if bool(args.url) == bool(args.report):
        parser.error('Supply a URL or one or more --report files')
    if min(args.max_assets, args.timeout, args.runs) <= 0 or args.runs > 10:
        parser.error('Limits must be positive')
    output = args.output_dir or Path('.scratch/lighthouse-check/artifacts') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error('Output directory must be empty; choose a fresh directory to preserve existing files')
    output.mkdir(parents=True, exist_ok=True)
    report = {'url': args.url, 'started_at': datetime.now(timezone.utc).isoformat(),
              'status': 'INCOMPLETE', 'errors': [], 'runs': [],
              'requested_runs': None if args.report or args.preflight_only else args.runs}
    try:
        if args.report:
            for index, source in enumerate(args.report, 1):
                content = source.read_text(encoding='utf-8-sig')
                assignment = re.search(r'window\.__LIGHTHOUSE_JSON__\s*=\s*', content)
                lhr = json.JSONDecoder().raw_decode(content[assignment.end():].lstrip())[0] if assignment else json.loads(content)
                filename = f'lighthouse-{index}.json'
                record = run_record(lhr, filename)
                (output / filename).write_text(json.dumps(lhr, ensure_ascii=False) + '\n')
                report['runs'].append(record)
            report['url'] = report['runs'][0]['final_url']
            report['status'] = 'REPORT_REVIEW'
        else:
            url = web_url(args.url)
            assets = [web_url(asset) for asset in args.asset]
            report['preflight'] = check(url, assets, timeout=args.timeout,
                                        max_assets=args.max_assets, include_external=True)
            if args.preflight_only:
                report['status'] = 'PREFLIGHT_ONLY'
            elif not report['preflight']['http_document_available']:
                report['errors'].append('The expected HTTP document is unavailable; resolve access before measuring')
            else:
                measure(web_url(args.url, keep_fragment=True), args, output, report)
    except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        report['errors'].append(str(error))
    finally:
        save(report, output, args.language)
    print(f'{report["status"]}: {output / "report.md"}')
    return 2 if report['status'] == 'INCOMPLETE' else 0


if __name__ == '__main__':
    raise SystemExit(main())
