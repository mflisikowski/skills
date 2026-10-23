#!/usr/bin/env python3
"""Inspect deployed compression with actual curl GETs before browser/Lighthouse checks."""

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urljoin, urlsplit, urlunsplit

from reporting import link, preflight_markdown


SAFE_HEADERS = {
    'content-type', 'content-encoding', 'content-length', 'vary', 'cache-control',
    'etag', 'last-modified', 'expires', 'server', 'age', 'x-cache', 'x-request-id', 'neuca-server', 'x-neuca-ray',
}
TEXT_TYPES = {
    'text/html', 'text/css', 'text/plain', 'text/javascript', 'application/javascript',
    'application/x-javascript', 'application/json', 'application/manifest+json',
    'image/svg+xml', 'application/xml', 'text/xml',
}
JS_TYPES = {'application/javascript', 'text/javascript', 'application/x-javascript'}


def web_url(value, *, keep_fragment=False):
    parsed = urlsplit(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('Expected an absolute HTTP(S) URL')
    if parsed.username or parsed.password:
        raise ValueError('Use a public test URL without credentials in the URL')
    return urlunsplit(parsed if keep_fragment else parsed._replace(fragment=''))


def headers_from_dump(text):
    result = {}
    for line in text.splitlines():
        if line.startswith('HTTP/'):
            result = {}
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            if key in SAFE_HEADERS:
                result[key] = ', '.join(filter(None, [result.get(key), value.strip()]))
    return result


def fetch(url, compressed, timeout):
    with tempfile.TemporaryDirectory(prefix='lighthouse-preflight-') as folder:
        headers_path, body_path = Path(folder) / 'headers', Path(folder) / 'body'
        command = [
            'curl', '--disable', '--silent', '--show-error', '--location',
            '--max-redirs', '5', '--proto', '=http,https', '--proto-redir', '=http,https',
            '--connect-timeout', str(min(5, timeout)), '--max-time', str(timeout),
            '--max-filesize', '20971520', '--dump-header', str(headers_path),
            '--output', str(body_path), '--write-out', '%{json}',
        ]
        command += ['--compressed'] if compressed else ['--header', 'Accept-Encoding: identity']
        command += ['--url', url]
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 5)
        except (OSError, subprocess.TimeoutExpired) as error:
            return {'url': url, 'error': str(error)}, b''
        if process.returncode:
            errors = process.stderr.strip().splitlines()
            return {'url': url, 'curl_exit': process.returncode,
                    'error': errors[-1] if errors else 'curl failed'}, b''
        try:
            meta = json.loads(process.stdout)
        except json.JSONDecodeError:
            return {'url': url, 'error': 'curl write-out JSON unavailable (requires curl 7.70+)'}, b''
        body = body_path.read_bytes()
        headers = headers_from_dump(headers_path.read_text(errors='replace'))
        result = {
            'url': meta['url_effective'], 'status': meta['http_code'], 'headers': headers,
            'downloaded_bytes': int(meta['size_download']), 'decoded_bytes': len(body),
            'sha256': hashlib.sha256(body).hexdigest(), 'seconds': meta['time_total'],
            'redirects': meta['num_redirects'],
            'http_version': meta['http_version'],
            'timings': {name: meta[key] for name, key in {
                'dns_seconds': 'time_namelookup', 'connect_seconds': 'time_connect',
                'tls_seconds': 'time_appconnect', 'first_byte_seconds': 'time_starttransfer',
            }.items()},
        }
        return result, body


class StartupAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.base = None
        self.assets = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'base' and self.base is None:
            self.base = attrs.get('href')
        if tag == 'script' and attrs.get('src'):
            self.assets.append((attrs['src'], 'js'))
        if tag == 'link' and attrs.get('href'):
            relations = set(attrs.get('rel', '').lower().split())
            if 'modulepreload' in relations or ('preload' in relations and attrs.get('as') == 'script'):
                self.assets.append((attrs['href'], 'js'))
            elif 'stylesheet' in relations or ('preload' in relations and attrs.get('as') == 'style'):
                self.assets.append((attrs['href'], 'css'))


def inspect(url, kind, threshold, timeout, page=None):
    compressed, body = page if page is not None else fetch(url, True, timeout)
    row = {'url': url, 'kind': kind, 'compressed': compressed, 'failures': [], 'warnings': []}
    if 'error' in compressed:
        row['inconclusive'] = True
        return row, body
    headers = compressed['headers']
    mime = headers.get('content-type', '').split(';')[0].strip().lower()
    if compressed['status'] != 200:
        row['failures'].append(f'Expected HTTP 200, got {compressed["status"]}')
        return row, body
    expected_types = {'html': {'text/html'}, 'js': JS_TYPES, 'css': {'text/css'}}
    if kind in expected_types and mime not in expected_types[kind]:
        row['failures'].append(f'Expected {kind} MIME, got {mime or "missing Content-Type"}')
        return row, body
    if kind == 'explicit' and mime == 'text/html':
        row['failures'].append('Explicit asset returned HTML; check SPA fallback or redirects')
        return row, body
    if kind == 'js':
        path = urlsplit(url).path
        if '/@vite/client' in path or path.endswith(('.tsx', '.ts', '.jsx')):
            row['failures'].append('Development entrypoint; use a deployed production build')
    encoding = headers.get('content-encoding', 'identity').lower().strip()
    text_asset = mime in TEXT_TYPES or mime.endswith('+json')
    row['encoding'] = encoding
    if not text_asset:
        row['warnings'].append('Not a known text MIME; HTTP compression is not required')
        return row, body
    if len(body) < threshold:
        row['exempt'] = f'Text smaller than {threshold} bytes'
        return row, body
    if encoding in {'', 'identity'}:
        row['failures'].append('Text response is not compressed')
    elif any(part.strip() not in {'gzip', 'br', 'deflate', 'zstd'} for part in encoding.split(',')):
        row['failures'].append(f'Unexpected content encoding: {encoding}')
    else:
        if 'accept-encoding' not in headers.get('vary', '').lower() and headers.get('vary') != '*':
            row['warnings'].append('Compressed response is missing Vary: Accept-Encoding')
        if compressed['downloaded_bytes'] >= len(body):
            row['warnings'].append('Encoding is present but does not reduce the downloaded body')
    row['saving_percent'] = round(100 * (1 - compressed['downloaded_bytes'] / len(body)), 1)

    if kind != 'html':
        identity, _ = fetch(url, False, timeout)
        row['identity'] = identity
        if 'error' in identity:
            row['inconclusive'] = True
        elif identity['status'] != 200:
            row['failures'].append(f'Identity request returned HTTP {identity["status"]}')
        elif identity['headers'].get('content-encoding', 'identity').strip().lower() not in {'', 'identity'}:
            row['failures'].append('Server sent encoded content despite Accept-Encoding: identity')
        elif identity['sha256'] != compressed['sha256']:
            if kind in {'js', 'css'}:
                row['failures'].append('Decoded and identity responses differ; verify representation/deployment stability')
            else:
                row['warnings'].append('Identity content changed; dynamic data cannot establish byte-for-byte equivalence')
    if kind == 'js':
        lines = body.splitlines()
        if len(lines) > 100 and len(body) / len(lines) < 120:
            row['warnings'].append('Possibly unminified JS; inspect build/source before concluding')
    return row, body


def check(url, assets, threshold=1024, timeout=15, max_assets=24, include_external=False):
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'requested_url': url,
              'scope': 'HTML, discovered startup JS/CSS ' + ('including cross-origin' if include_external else 'from the same origin') + ', and explicit URLs',
              'include_external': include_external,
              'warnings': [], 'rows': [], 'skipped_assets': []}
    version = subprocess.run(['curl', '--version'], capture_output=True, text=True, check=True)
    report['curl_version'] = version.stdout.splitlines()[0]
    page = fetch(url, True, timeout)
    row, html = inspect(url, 'html', threshold, timeout, page)
    report['rows'].append(row)
    coverage_incomplete = False
    content_type = row['compressed'].get('headers', {}).get('content-type', '').split(';')[0].strip().lower()
    if not row.get('inconclusive') and row['compressed'].get('status') == 200 and content_type == 'text/html':
        parser = StartupAssets()
        parser.feed(html.decode('utf-8', errors='replace'))
        final_url = row['compressed']['url']
        base = urljoin(final_url, parser.base or final_url)
        origin = urlsplit(final_url)[:2]
        urls = {}
        external = set()
        for path, kind in parser.assets:
            resolved = urljoin(base, path)
            if urlsplit(resolved).scheme not in {'http', 'https'}:
                continue
            if urlsplit(resolved)[:2] != origin:
                external.add(resolved)
                if not include_external:
                    continue
            urls[resolved] = kind
        for asset in assets:
            path = urlsplit(asset).path
            kind = 'js' if path.endswith(('.js', '.mjs', '.tsx', '.ts', '.jsx')) else 'css' if path.endswith('.css') else 'explicit'
            urls[asset] = urls.get(asset, kind)
        report['skipped_assets'] = sorted(external.difference(urls))
        if report['skipped_assets']:
            coverage_incomplete = True
            report['warnings'].append('External startup assets were not probed; coverage is incomplete')
        if not urls:
            coverage_incomplete = True
            report['warnings'].append('No startup JS/CSS found; inspect browser discovery or supply --asset URLs')
        if len(urls) > max_assets:
            coverage_incomplete = True
            report['skipped_assets'].extend(list(urls)[max_assets:])
            report['warnings'].append(f'Discovered {len(urls)} assets, probing only {max_assets}; increase --max-assets')
        for asset, kind in list(urls.items())[:max_assets]:
            result, _ = inspect(asset, kind, threshold, timeout)
            report['rows'].append(result)

    if any(r['failures'] for r in report['rows']):
        verdict = 'BLOCKED'
    elif coverage_incomplete or any(r.get('inconclusive') for r in report['rows']):
        verdict = 'INCONCLUSIVE'
    else:
        verdict = 'PASS'
    report['http_document_available'] = not row.get('inconclusive') and (
        row['compressed'].get('status') == 200 and content_type == 'text/html')
    report['coverage_complete'] = report['http_document_available'] and not coverage_incomplete and not any(
        r.get('inconclusive') for r in report['rows'])
    report['verdict'] = verdict
    report['next_step'] = {'PASS': 'Browser smoke check and resolve warnings before Lighthouse acceptance',
                           'BLOCKED': 'Fix failed HTTP/compression checks before Lighthouse acceptance',
                           'INCONCLUSIVE': 'Restore access or complete asset coverage before deciding'}[verdict]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--asset', action='append', default=[], help='Additional dynamic chunk/CDN/API URL')
    parser.add_argument('--output', type=Path, help='Write structured JSON evidence')
    parser.add_argument('--language', choices=['en', 'pl'], default='en')
    parser.add_argument('--include-external', action='store_true', help='Probe discovered cross-origin startup assets within the same limits')
    parser.add_argument('--min-bytes', type=int, default=1024)
    parser.add_argument('--timeout', type=int, default=15, help='Maximum seconds per GET')
    parser.add_argument('--max-assets', type=int, default=24)
    args = parser.parse_args()
    if min(args.min_bytes, args.timeout, args.max_assets) <= 0:
        parser.error('Limits must be positive')
    if not shutil.which('curl'):
        parser.error('curl is required')
    try:
        url = web_url(args.url)
        assets = [web_url(asset) for asset in args.asset]
    except ValueError as error:
        parser.error(str(error))
    report = check(url, assets, args.min_bytes, args.timeout, args.max_assets, args.include_external)
    print(f'{report["verdict"]}: {report["next_step"]}')
    print('encoding | downloaded / decoded bytes | result | URL')
    for row in report['rows']:
        response = row['compressed']
        outcome = 'INCONCLUSIVE' if row.get('inconclusive') else 'FAIL' if row['failures'] else 'OK'
        print(f'{row.get("encoding", "-")} | {response.get("downloaded_bytes", "-")} / '
              f'{response.get("decoded_bytes", "-")} | {outcome} | {row["url"]}')
        for message in row['failures'] + row['warnings']:
            print(f'  - {message}')
        if response.get('error'):
            print(f'  - {response["error"]}')
    for warning in report['warnings']:
        print(f'WARNING: {warning}')
    output = args.output or Path('.scratch/lighthouse-check/artifacts') / (
        datetime.now(timezone.utc).strftime('preflight-%Y%m%dT%H%M%S%fZ.json'))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    markdown = output.with_suffix('.md') if output.suffix.lower() != '.md' else output.with_name(output.name + '.md')
    markdown.write_text(preflight_markdown(report, args.language) + '\n' + link(output.name) + '\n')
    print(f'Evidence: {output}\nReport: {markdown}')
    return {'PASS': 0, 'BLOCKED': 1, 'INCONCLUSIVE': 2}[report['verdict']]


if __name__ == '__main__':
    sys.exit(main())
