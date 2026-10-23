#!/usr/bin/env python3
"""Contract tests: real HTTP fixture server and the actual curl CLI, without Internet."""

import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from threading import Thread
import unittest


SCRIPT = Path(__file__).with_name('preflight.py')
JS = b'const message="production";console.log(message);' * 300
CSS = b'.card{display:flex;color:purple;}' * 120


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/ok.html')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        status, mime, body = 200, 'application/javascript', JS
        if self.path.endswith('.html'):
            mime = 'text/html'
            asset = {
                '/ok.html': '/app.js', '/plain.html': '/plain.js',
                '/vary-only.html': '/vary-only.js', '/novary.html': '/novary.js',
                '/mismatch.html': '/mismatch.js', '/wrong-mime.html': '/wrong.js',
                '/tiny.html': '/tiny.js', '/broken-gzip.html': '/broken.js',
                '/missing.html': '/missing.js', '/dev.html': '/src/main.tsx',
                '/identity-encoded.html': '/identity-encoded.js',
            }.get(self.path, '/app.js')
            body = f'<html><head><script type="module" src="{asset}"></script><link rel="stylesheet" href="/app.css"></head><body>test</body></html>'.encode()
            if self.path == '/empty.html':
                body = b'<html><body>No startup assets</body></html>'
            if self.path == '/external.html':
                body += f'<script src="http://localhost:{self.server.server_port}/app.js"></script>'.encode()
        elif self.path == '/app.css':
            mime, body = 'text/css', CSS
        elif self.path == '/tiny.js':
            body = b'console.log("tiny");'
        elif self.path == '/src/main.tsx':
            body = b'console.log("development");'
        elif self.path == '/wrong.js':
            mime, body = 'text/html', b'<html>SPA fallback</html>'
        elif self.path == '/missing.js':
            status = 404
        elif self.path == '/mismatch.js' and self.headers.get('Accept-Encoding') == 'identity':
            body = b'console.log("different response");' * 300
        elif self.path == '/api/data':
            mime, body = 'application/json', b'{"values":[' + b'1,' * 2000 + b'0]}'
        elif self.path == '/api/dynamic':
            value = b'1' if self.headers.get('Accept-Encoding') == 'identity' else b'2'
            mime, body = 'application/json', b'{"values":[' + (value + b',') * 2000 + b'0]}'
        elif self.path == '/readable.js':
            body = b'console.log("readable source");\n' * 200
        elif self.path == '/asset-fallback':
            mime, body = 'text/html', b'<html>wrong asset</html>' * 100
        elif self.path == '/image.avif':
            mime, body = 'image/avif', b'fixture-binary-data' * 100

        compress = 'gzip' in self.headers.get('Accept-Encoding', '')
        compress = compress and self.path not in {'/plain.js', '/vary-only.js', '/tiny.js', '/image.avif'}
        if self.path == '/identity-encoded.js':
            compress = True
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Set-Cookie', 'secret=do-not-store')
        if self.path != '/novary.js':
            self.send_header('Vary', 'Accept-Encoding')
        if compress:
            self.send_header('Content-Encoding', 'gzip')
            body = b'not-gzip' if self.path == '/broken.js' else gzip.compress(body)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def probe(self, path, *extra):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'evidence.json'
            process = subprocess.run([sys.executable, str(SCRIPT), self.base + path,
                                      '--output', str(output), '--timeout', '2', *extra],
                                     capture_output=True, text=True, timeout=15)
            self.assertTrue(output.exists(), process.stderr)
            return process, json.loads(output.read_text())

    def test_compression_is_measured_and_decodes_to_identity(self):
        process, report = self.probe('/ok.html')
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertEqual(report['verdict'], 'PASS')
        js = next(row for row in report['rows'] if row['kind'] == 'js')
        self.assertEqual(js['compressed']['decoded_bytes'], len(JS))
        self.assertLess(js['compressed']['downloaded_bytes'], len(JS) / 2)
        self.assertEqual(js['compressed']['sha256'], js['identity']['sha256'])
        self.assertNotIn('secret', json.dumps(report))

    def test_uncompressed_js_blocks(self):
        process, report = self.probe('/plain.html')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(report['verdict'], 'BLOCKED')

    def test_skipped_external_asset_prevents_complete_coverage(self):
        process, report = self.probe('/external.html')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(report['verdict'], 'INCONCLUSIVE')
        self.assertFalse(report['coverage_complete'])
        external = f'http://localhost:{self.server.server_port}/app.js'
        self.assertIn(external, report['skipped_assets'])
        process, report = self.probe('/external.html', '--asset', external)
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertTrue(report['coverage_complete'])
        self.assertEqual(report['skipped_assets'], [])

    def test_external_discovery_can_be_completed_by_agent_within_limits(self):
        process, report = self.probe('/external.html', '--include-external')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(report['coverage_complete'])
        self.assertEqual(len(report['rows']), 4)
        process, report = self.probe('/external.html', '--include-external', '--max-assets', '1')
        self.assertEqual(process.returncode, 2)
        self.assertFalse(report['coverage_complete'])
        self.assertEqual(len(report['skipped_assets']), 2)

    def test_markdown_and_http_measurements_exist_for_all_verdicts(self):
        for path, expected in [('/ok.html', 'PASS'), ('/plain.html', 'BLOCKED'),
                               ('/external.html', 'INCONCLUSIVE')]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'preflight.json'
                process = subprocess.run([sys.executable, str(SCRIPT), self.base + path,
                                          '--output', str(output), '--language', 'pl'],
                                         capture_output=True, text=True, timeout=15)
                self.assertTrue(output.exists(), process.stderr)
                report = json.loads(output.read_text())
                self.assertEqual(report['verdict'], expected)
                markdown = output.with_suffix('.md').read_text()
                self.assertIn(self.base + path, markdown)
                self.assertIn(expected, markdown)
                response = report['rows'][0]['compressed']
                self.assertGreaterEqual(response['timings']['first_byte_seconds'], 0)
                self.assertIn(response['http_version'], {'1', '1.0', '1.1', '2', '3'})
                self.assertTrue(report['http_document_available'])

    def test_vary_alone_does_not_pass(self):
        process, report = self.probe('/vary-only.html')
        self.assertEqual(process.returncode, 1)
        self.assertTrue(any('not compressed' in failure for row in report['rows'] for failure in row['failures']))

    def test_missing_vary_is_a_cache_warning(self):
        process, report = self.probe('/novary.html')
        self.assertEqual(process.returncode, 0)
        self.assertTrue(any('Vary' in warning for row in report['rows'] for warning in row['warnings']))

    def test_different_representations_block(self):
        process, report = self.probe('/mismatch.html')
        self.assertEqual(process.returncode, 1)
        self.assertTrue(any('responses differ' in failure for row in report['rows'] for failure in row['failures']))

    def test_html_instead_of_javascript_blocks(self):
        process, report = self.probe('/wrong-mime.html')
        self.assertEqual(process.returncode, 1)
        self.assertTrue(any('MIME' in failure for row in report['rows'] for failure in row['failures']))

    def test_small_text_and_binary_are_exempt(self):
        process, report = self.probe('/tiny.html', '--asset', self.base + '/image.avif')
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertTrue(any(row.get('exempt') for row in report['rows']))

    def test_corrupt_encoded_body_is_inconclusive(self):
        process, report = self.probe('/broken-gzip.html')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(report['verdict'], 'INCONCLUSIVE')

    def test_http_error_blocks(self):
        process, _ = self.probe('/missing.html')
        self.assertEqual(process.returncode, 1)

    def test_asset_limit_and_absent_discovery_cannot_pass(self):
        for path, extra in [('/ok.html', ['--max-assets', '1']), ('/empty.html', [])]:
            with self.subTest(path=path):
                process, report = self.probe(path, *extra)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(report['verdict'], 'INCONCLUSIVE')

    def test_redirects_and_explicit_api_assets(self):
        process, report = self.probe('/redirect', '--asset', self.base + '/api/data')
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertEqual(report['rows'][0]['compressed']['redirects'], 1)
        self.assertEqual(report['rows'][-1]['encoding'], 'gzip')

    def test_explicit_asset_spa_fallback_blocks(self):
        process, _ = self.probe('/ok.html', '--asset', self.base + '/asset-fallback')
        self.assertEqual(process.returncode, 1)

    def test_dynamic_api_changes_are_not_treated_as_static_corruption(self):
        process, report = self.probe('/ok.html', '--asset', self.base + '/api/dynamic')
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertTrue(any('dynamic data' in warning for row in report['rows'] for warning in row['warnings']))

    def test_minification_is_a_hint_separate_from_compression(self):
        process, report = self.probe('/ok.html', '--asset', self.base + '/readable.js')
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertTrue(any('unminified' in warning for row in report['rows'] for warning in row['warnings']))

    def test_development_entrypoint_blocks_even_if_small(self):
        process, report = self.probe('/dev.html')
        self.assertEqual(process.returncode, 1)
        self.assertTrue(any('Development' in failure for row in report['rows'] for failure in row['failures']))

    def test_ignoring_identity_negotiation_blocks(self):
        process, report = self.probe('/identity-encoded.html')
        self.assertEqual(process.returncode, 1)

    def test_connection_failure_is_not_a_compression_verdict(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            unused_port = sock.getsockname()[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'evidence.json'
            process = subprocess.run([sys.executable, str(SCRIPT), f'http://127.0.0.1:{unused_port}/',
                                      '--output', str(output), '--timeout', '1'], capture_output=True, timeout=10)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(json.loads(output.read_text())['verdict'], 'INCONCLUSIVE')


if __name__ == '__main__':
    unittest.main(verbosity=2)
