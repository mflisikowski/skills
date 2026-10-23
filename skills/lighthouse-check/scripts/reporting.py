"""Render evidence as Markdown; measurements remain in the accompanying JSON."""

from pathlib import Path
import json
import math
import re
from statistics import median
from urllib.parse import quote


METRICS = {
    'first-contentful-paint': 'FCP', 'largest-contentful-paint': 'LCP',
    'total-blocking-time': 'TBT', 'cumulative-layout-shift': 'CLS',
    'speed-index': 'Speed Index', 'total-byte-weight': 'Transfer',
}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def run_record(lhr, filename):
    if not isinstance(lhr, dict) or not isinstance(lhr.get('audits'), dict) or not isinstance(lhr.get('lighthouseVersion'), str):
        raise ValueError('Not a Lighthouse JSON report')
    for field in ['configSettings', 'environment', 'categories']:
        if field in lhr and not isinstance(lhr[field], dict):
            raise ValueError(f'Invalid Lighthouse report field: {field}')
    warnings = lhr.get('runWarnings', [])
    if not isinstance(warnings, list) or any(not isinstance(warning, str) for warning in warnings):
        raise ValueError('Invalid Lighthouse report field: runWarnings')
    record = {
        'file': filename, 'fetch_time': lhr.get('fetchTime'), 'version': lhr['lighthouseVersion'],
        'final_url': lhr.get('finalDisplayedUrl', lhr.get('finalUrl')),
        'config': lhr.get('configSettings', {}), 'environment': lhr.get('environment', {}),
        'user_agent': lhr.get('userAgent'), 'runtime_error': lhr.get('runtimeError'),
        'warnings': lhr.get('runWarnings', []), 'metrics': {}, 'scores': {}, 'findings': [],
    }
    if record['runtime_error']:
        return record
    for key, audit in lhr['audits'].items():
        if not isinstance(audit, dict):
            continue
        if key in METRICS and number(audit.get('numericValue')):
            if not isinstance(audit.get('numericUnit', ''), str):
                raise ValueError(f'Invalid metric unit: {key}')
            record['metrics'][key] = {'value': audit['numericValue'], 'unit': audit.get('numericUnit', '')}
        elif number(audit.get('score')) and audit['score'] < 1:
            details = audit.get('details') or {}
            if not isinstance(details, dict):
                details = {}
            savings = details.get('overallSavingsMs', 0)
            record['findings'].append({'id': key, 'title': audit.get('title', key),
                                       'description': audit.get('description', ''),
                                       'display_value': audit.get('displayValue', ''),
                                       'savings_ms': savings if number(savings) else 0})
    for key, category in (lhr.get('categories') or {}).items():
        if isinstance(category, dict) and number(category.get('score')):
            record['scores'][key] = category['score'] * 100
    return record


def summarize(runs):
    successful = [run for run in runs if not run.get('runtime_error')]
    signatures = {json_signature(run) for run in successful}
    comparable = bool(successful) and len(signatures) == 1
    result = {'comparable': comparable, 'successful_runs': len(successful), 'metrics': {}, 'scores': {}}
    if not comparable:
        return result
    for kind in ['metrics', 'scores']:
        keys = set.intersection(*(set(run[kind]) for run in successful))
        for key in sorted(keys):
            values = [run[kind][key]['value'] if kind == 'metrics' else run[kind][key] for run in successful]
            if kind == 'metrics' and len({run[kind][key]['unit'] for run in successful}) != 1:
                continue
            result[kind][key] = {'median': median(values), 'min': min(values), 'max': max(values)}
            if kind == 'metrics':
                result[kind][key]['unit'] = successful[0][kind][key]['unit']
    return result


def json_signature(run):
    return json.dumps([run['final_url'], run['version'], run['config'], run.get('user_agent'),
                       run.get('environment', {}).get('hostUserAgent')], sort_keys=True)


def lighthouse_markdown(report, language):
    pl = language == 'pl'
    choose = lambda en, polish: polish if pl else en
    lines = [choose('## Lighthouse measurements', '## Pomiary Lighthouse'), '',
             f'{choose("Valid measurements", "Poprawne pomiary")}: {report["summary"]["successful_runs"]}; '
             f'{choose("requested", "zlecone")}: {report.get("requested_runs", "—")}.', '']
    runs = report.get('runs', [])
    if not runs:
        return '\n'.join(lines + [choose('No Lighthouse measurement was collected. No score is assigned.',
                                          'Nie zebrano pomiaru Lighthouse. Wynik punktowy nie został przypisany.'), ''])
    for index, run in enumerate(runs, 1):
        lines += [f'### {choose("Run", "Próba")} {index}', '',
                  f'- UTC: {text(run.get("fetch_time"))}',
                  f'- URL: {text(run.get("final_url"))}',
                  f'- Lighthouse: {text(run["version"])}',
                  f'- {choose("Device", "Urządzenie")}: {text(run["config"].get("formFactor"))}',
                  f'- {choose("Throttling method", "Metoda ograniczania zasobów")}: {text(run["config"].get("throttlingMethod"))}',
                  f'- {choose("Source", "Źródło")}: {link(run["file"])}', '']
        if run.get('runtime_error'):
            lines += [f'**{text(run["runtime_error"])}**', '']
        else:
            lines += [choose('| Metric | Value |', '| Metryka | Wartość |'), '| --- | --- |']
            lines += [f'| {text(key)} | {value:.2f} / 100 |' for key, value in run['scores'].items()]
            lines += [f'| {METRICS[key]} | {value["value"]:.3f} {text(value["unit"])} |'
                      for key, value in run['metrics'].items()]
            lines += ['']
        lines += [f'- {text(warning)}' for warning in run.get('warnings', [])]
    summary = report['summary']
    if summary['comparable']:
        lines += ['', choose('### Median and range', '### Mediana i rozrzut'), '',
                  choose('| Metric | Median | Min | Max | Unit |', '| Metryka | Mediana | Min | Max | Jednostka |'), '| --- | --- | --- | --- | --- |']
        for key, value in {**summary['scores'], **summary['metrics']}.items():
            lines += [f'| {METRICS.get(key, text(key))} | {value["median"]:.3f} | {value["min"]:.3f} | '
                      f'{value["max"]:.3f} | {text(value.get("unit", "/100"))} |']
    else:
        lines += ['', choose('Reports have different URLs, versions or settings, or contain no valid measurements. They were not aggregated.',
                             'Raporty mają różne adresy, wersje lub ustawienia albo nie zawierają poprawnych pomiarów. Nie połączono ich w medianę.')]
    lines += ['', choose('### Findings and next actions', '### Ustalenia i dalsze działania'), '']
    findings = {}
    for run in runs:
        for finding in run['findings']:
            findings.setdefault(finding['id'], finding)
    for finding in sorted(findings.values(), key=lambda item: -item.get('savings_ms', 0))[:20]:
        priority = 'P2' if finding.get('savings_ms', 0) > 0 else 'P3'
        lines += [f'- **{priority}: {text(finding["title"])}** ({text(finding["id"])}): '
                  f'{text(finding["display_value"])} {text(finding["description"])}']
    lines += ['', choose('Provisional priorities: P2 has quantified time savings; P3 needs contextual assessment. Estimated savings are not additive. After a change, repeat the same scenario and compare matching measurements. Full details are in the JSON files.',
                         'Wstępne priorytety: P2 ma oszacowaną oszczędność czasu, P3 wymaga oceny kontekstu. Szacowanych oszczędności nie należy sumować. Po zmianie powtórz ten sam scenariusz i porównaj pomiary przy zgodnych ustawieniach. Pełne szczegóły znajdują się w JSON.'), '',
              choose('Matching report settings do not prove identical hardware or network conditions. Laboratory results do not replace real-user data.',
                     'Zgodność ustawień raportów nie dowodzi zgodności sprzętu i sieci. Wyniki laboratoryjne nie zastępują danych rzeczywistych użytkowników.'), '']
    return '\n'.join(lines)


def text(value):
    value = str(value).replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
    for char in '`[]<>|*#':
        value = value.replace(char, '\\' + char)
    return value


def link(path, label=None):
    return f'[{text(label or Path(path).name)}]({quote(str(path), safe="/.")})'


def cache_note(headers, language):
    pl = language == 'pl'
    control = headers.get('cache-control', '').lower()
    directives = {part.strip().split('=', 1)[0] for part in control.split(',')}
    notes = []
    if 'no-store' in directives:
        notes.append('zapis w cache zabroniony' if pl else 'storage forbidden')
    if 'no-cache' in directives:
        notes.append('ponowne użycie wymaga rewalidacji' if pl else 'reuse requires revalidation')
    if 'private' in directives:
        notes.append('cache współdzielony zabroniony' if pl else 'shared caching forbidden')
    age = re.search(r'(?:^|,)\s*max-age\s*=\s*"?(\d+)', control)
    if age:
        notes.append(f'max-age: {age[1]} s')
    if not control:
        notes.append('brak jawnego Cache-Control; możliwe cache heurystyczne' if pl
                     else 'no explicit Cache-Control; heuristic caching may apply')
    return '; '.join(notes) or ('polityka wymaga oceny kontekstu' if pl else 'evaluate policy in context')


def recommendation(message, language):
    pl = language == 'pl'
    if 'not compressed' in message or 'Vary' in message:
        return ('Sprawdź kompresję i negocjację wariantów na publicznym adresie; powtórz GET i porównaj bajty.' if pl
                else 'Check compression and representation negotiation at the public URL; repeat GET and compare bytes.')
    if 'differ' in message or 'identity' in message.lower():
        return ('Sprawdź stabilność wdrożenia i wariantów odpowiedzi; powtórz oba żądania dla tego samego zasobu.' if pl
                else 'Check deployment and representation stability; repeat both requests for the same resource.')
    if 'minified' in message or 'Development' in message:
        return ('Sprawdź konfigurację produkcyjnego builda; potwierdź wdrożone pliki i ponów kontrolę.' if pl
                else 'Inspect the production build configuration; verify deployed assets and repeat the check.')
    return ('Sprawdź dostęp, oczekiwaną treść i konfigurację wskazanego zasobu; powtórz kontrolę.' if pl
            else 'Check access, expected content and the resource configuration; repeat the check.')


def preflight_markdown(report, language='en'):
    pl = language == 'pl'
    choose = lambda en, polish: polish if pl else en
    lines = [choose('# HTTP preflight', '# Kontrola dostarczania strony'), '',
             f'- URL: {text(report["requested_url"])}',
             f'- UTC: {text(report["checked_at"])}',
             f'- {choose("Transport verdict", "Ocena transportu")}: **{report["verdict"]}**',
             f'- {choose("Coverage complete within the declared scope", "Kompletne pokrycie zadeklarowanego zakresu")}: '
             f'**{report.get("coverage_complete", False)}**',
             f'- {choose("HTTP document available", "Dokument HTTP dostępny")}: '
             f'**{report.get("http_document_available", False)}**',
             f'- curl: {text(report.get("curl_version", "unavailable"))}', '',
             choose('HTTP availability does not confirm the browser scenario. Transport failures do not automatically prevent a diagnostic baseline.',
                    'Dostępność HTTP nie potwierdza scenariusza w przeglądarce. Usterki transportu nie wykluczają automatycznie pomiaru diagnostycznego.'), '',
             choose('## Evidence', '## Dowody'), '',
             choose('| URL | HTTP / MIME | Encoding | Downloaded / decoded B | TTFB / total s | Protocol |',
                    '| URL | HTTP / MIME | Kodowanie | Pobrano / odkodowano B | TTFB / całość s | Protokół |'),
             '| --- | --- | --- | --- | --- | --- |']
    for row in report['rows']:
        response = row['compressed']
        headers = response.get('headers', {})
        times = response.get('timings', {})
        lines.append(f'| {text(row["url"])} | {response.get("status", "-")} / '
                     f'{text(headers.get("content-type", "-"))} | {text(row.get("encoding", "-"))} | '
                     f'{response.get("downloaded_bytes", "-")} / {response.get("decoded_bytes", "-")} | '
                     f'{times.get("first_byte_seconds", "-")} / {response.get("seconds", "-")} | '
                     f'{text(response.get("http_version", "-"))} |')
    lines += ['', choose('TTFB and total are curl client timings, not isolated server processing or Lighthouse metrics.',
                         'TTFB i czas całkowity pochodzą z klienta curl; nie są czasem samej aplikacji serwerowej ani metrykami Lighthouse.'), '',
              choose('## Findings and verification', '## Ustalenia i weryfikacja poprawek'), '']
    findings = 0
    for row in report['rows']:
        for message in row['failures'] + row['warnings'] + ([row['compressed']['error']] if 'error' in row['compressed'] else []):
            findings += 1
            lines += [f'- **{text(row["url"])}**: {text(message)} '
                      f'{recommendation(message, language)}']
    if not findings:
        lines += [choose('No issues detected in the probed responses.', 'W zbadanych odpowiedziach nie wykryto usterek.')]
    lines += ['', choose('## Observed cache policies', '## Obserwowane polityki cache'), '']
    for row in report['rows']:
        headers = row['compressed'].get('headers', {})
        lines += [f'- {text(row["url"])}: {text(headers.get("cache-control", "(absent)"))}; '
                  f'{cache_note(headers, language)}.']
    lines += ['', choose('Cache policies need content context: versioned assets, HTML and personalized responses have different requirements. Revalidation was not tested.',
                         'Politykę trzeba odnieść do treści: zasoby wersjonowane, HTML i odpowiedzi prywatne mają różne wymagania. Nie testowano rewalidacji.'), '',
              choose('## Scope and limitations', '## Zakres i ograniczenia'), '',
              ('HTML, wykryte startowe JS/CSS ' + ('także z innych źródeł' if report.get('include_external') else 'z tego samego źródła') + ' i jawnie wskazane adresy.' if pl else text(report['scope'])), '',
              choose('The scan does not execute JavaScript or crawl routes, CSS dependencies, images or fonts. An empty discovery cannot establish complete coverage. Codec support is limited to the installed curl.',
                     'Skan nie wykonuje JavaScriptu ani nie przegląda podstron, zależności CSS, obrazów i fontów. Brak odkrytych zasobów nie potwierdza kompletności. Zakres kodeków zależy od zainstalowanego curl.')]
    for warning in report.get('warnings', []):
        lines.append(f'- {text(warning)}')
    for url in report.get('skipped_assets', []):
        lines.append(f'- {choose("Not probed", "Nie zbadano")}: {text(url)}')
    return '\n'.join(lines) + '\n'
