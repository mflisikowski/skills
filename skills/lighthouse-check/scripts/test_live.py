#!/usr/bin/env python3
"""Opt-in contract test using real Lighthouse, Chrome and a relocated skill."""

import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Thread
import unittest


TOOLS = os.environ.get('LIGHTHOUSE_TEST_TOOLS')
PAYLOAD = b'window.auditFixture=' + json.dumps('production payload ' * 20000).encode() + b';'


class LiveHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.endswith('/app.js'):
            mime, body = 'application/javascript', PAYLOAD
        else:
            mime = 'text/html'
            body = b'<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Audit fixture</title><script defer src="app.js"></script></head><body><main><h1>Audit fixture ready</h1><p>Production content for a controlled measurement.</p></main></body></html>'
            body += b'<script>if(location.hash==="#/target"){document.querySelector("h1").textContent="Hash target ready"}</script>'
        encoded = self.path.startswith('/compressed/') and 'gzip' in self.headers.get('Accept-Encoding', '')
        if encoded:
            body = gzip.compress(body)
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Vary', 'Accept-Encoding')
        if encoded:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@unittest.skipUnless(TOOLS, 'Set LIGHTHOUSE_TEST_TOOLS to an installed Lighthouse package root')
class LiveAuditTests(unittest.TestCase):
    def test_fragment_route_is_retained_for_browser_and_lighthouse(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), LiveHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                url = f'http://127.0.0.1:{server.server_port}/compressed/#/target'
                process = subprocess.run([sys.executable, str(Path(__file__).with_name('audit.py')), url,
                                          '--runs', '1', '--tools-dir', str(Path(TOOLS).resolve()),
                                          '--output-dir', directory, '--expected-text', 'Hash target ready'],
                                         capture_output=True, text=True, timeout=150)
                self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
                report = json.loads((Path(directory) / 'audit.json').read_text())
                self.assertEqual(report['browser']['final_url'], url)
                self.assertEqual(report['runs'][0]['final_url'], url)
                self.assertNotIn('#', report['preflight']['requested_url'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_wrong_content_and_missing_chrome_produce_incomplete_reports(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), LiveHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for options in [
                ['--expected-text', 'This marker is deliberately absent'],
                ['--chrome-path', '/definitely-missing-audit-chrome'],
            ]:
                with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                    command = [sys.executable, str(Path(__file__).with_name('audit.py')),
                               f'http://127.0.0.1:{server.server_port}/compressed/', '--runs', '1',
                               '--tools-dir', str(Path(TOOLS).resolve()), '--output-dir', directory, *options]
                    process = subprocess.run(command, capture_output=True, text=True, timeout=90)
                    self.assertEqual(process.returncode, 2, process.stderr + process.stdout)
                    report = json.loads((Path(directory) / 'audit.json').read_text())
                    self.assertEqual(report['status'], 'INCOMPLETE')
                    self.assertEqual(report['runs'], [])
                    self.assertTrue(report['errors'])
                    self.assertTrue((Path(directory) / 'report.md').is_file())
                    self.assertFalse(report['summary']['comparable'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_real_audit_runs_after_relocation_and_measures_compression_variants(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), LiveHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                skill = root / 'relocated skill'
                shutil.copytree(Path(__file__).resolve().parents[1], skill,
                                ignore=shutil.ignore_patterns('__pycache__'))
                artifact_root = Path(os.environ.get('LIGHTHOUSE_TEST_OUTPUT', str(root / 'results')))
                evidence = []
                for variant in ['compressed', 'plain']:
                    output = artifact_root / variant
                    command = [sys.executable, str(skill / 'scripts/audit.py'),
                               f'http://127.0.0.1:{server.server_port}/{variant}/',
                               '--output-dir', str(output),
                               '--language', 'pl', '--expected-text', 'Audit fixture ready']
                    if variant != 'plain' or not os.environ.get('LIGHTHOUSE_TEST_BOOTSTRAP'):
                        command += ['--tools-dir', str(Path(TOOLS).resolve())]
                    if variant == 'plain':
                        command += ['--runs', '1', '--device', 'desktop']
                    process = subprocess.run(command, capture_output=True, text=True, timeout=420, cwd=root)
                    self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
                    report = json.loads((output / 'audit.json').read_text())
                    self.assertEqual(report['status'], 'COMPLETED', report['errors'])
                    expected_runs = 3 if variant == 'compressed' else 1
                    self.assertEqual(len(report['runs']), expected_runs)
                    self.assertTrue(report['browser']['ready'])
                    self.assertTrue((output / 'browser.png').is_file())
                    self.assertTrue((output / 'report.md').is_file())
                    if variant == 'plain' and os.environ.get('LIGHTHOUSE_TEST_BOOTSTRAP'):
                        self.assertTrue((output / 'install.log').is_file())
                    self.assertIn('largest-contentful-paint', report['summary']['metrics'])
                    self.assertEqual(report['runs'][0]['config']['formFactor'],
                                     'mobile' if variant == 'compressed' else 'desktop')
                    for run in report['runs']:
                        self.assertTrue((output / run['file']).is_file())
                    js = next(row for row in report['preflight']['rows'] if row['kind'] == 'js')
                    evidence.append(js['compressed']['downloaded_bytes'])
                    self.assertEqual(report['preflight']['verdict'], 'PASS' if variant == 'compressed' else 'BLOCKED')
                self.assertLess(evidence[0], evidence[1] / 10)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main(verbosity=2)
