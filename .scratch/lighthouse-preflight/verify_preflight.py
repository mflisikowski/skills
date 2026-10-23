#!/usr/bin/env python3
"""Verify corrected cross-origin startup coverage using local HTTP fixtures."""

import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).with_name('evidence')
HELPER = ROOT / 'skills/lighthouse-check/scripts/preflight.py'
JS = b'console.log("production fixture");' * 300
CSS = b'body{color:purple;}' * 300


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            mime = 'text/html'
            body = (
                '<!doctype html><html><head>'
                '<link rel="stylesheet" href="/app.css">'
                '<script src="/app.js" defer></script>'
                f'<script src="{self.server.cdn_url}/cdn.js" defer></script>'
                '</head><body><h1>Local audit fixture</h1></body></html>'
            ).encode()
        else:
            mime = 'text/css' if self.path == '/app.css' else 'application/javascript'
            body = CSS if self.path == '/app.css' else JS
        encoded = self.path != '/cdn.js' and 'gzip' in self.headers.get('Accept-Encoding', '')
        if encoded:
            body = gzip.compress(body)
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Vary', 'Accept-Encoding')
        if encoded:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    EVIDENCE.mkdir(exist_ok=True)
    servers = []
    threads = []
    try:
        for _ in range(2):
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            servers.append(server)
        cdn_url = f'http://127.0.0.1:{servers[0].server_port}'
        page_url = f'http://127.0.0.1:{servers[1].server_port}/'
        for server in servers:
            server.cdn_url = cdn_url
            thread = Thread(target=server.serve_forever, daemon=True)
            threads.append(thread)
            thread.start()
        outcomes = []
        for name, extra in (
            ('discovery-only', []),
            ('explicit-cdn', ['--asset', cdn_url + '/cdn.js']),
        ):
            output = EVIDENCE / f'{name}.json'
            command = [sys.executable, str(HELPER), page_url,
                       '--timeout', '2', '--output', str(output), *extra]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if not output.exists():
                raise RuntimeError(result.stderr or result.stdout)
            report = json.loads(output.read_text())
            outcome = {
                'case': name, 'exit': result.returncode, 'verdict': report['verdict'],
                'checked_urls': [row['url'] for row in report['rows']],
                'warnings': report['warnings'],
                'failures': [failure for row in report['rows'] for failure in row['failures']],
            }
            outcomes.append(outcome)
            print(json.dumps(outcome, ensure_ascii=False))
        (EVIDENCE / 'summary.json').write_text(json.dumps(outcomes, indent=2) + '\n')
        observed = [(outcome['verdict'], outcome['exit']) for outcome in outcomes]
        if observed != [('INCONCLUSIVE', 2), ('BLOCKED', 1)]:
            raise RuntimeError(f'Reproduction changed: {observed}')
        print('Confirmed: skipping an external startup script prevents PASS; probing it reveals the transport defect.')
    finally:
        for server, thread in zip(servers, threads):
            server.shutdown()
            server.server_close()
            thread.join()
        for server in servers[len(threads):]:
            server.server_close()


if __name__ == '__main__':
    main()
