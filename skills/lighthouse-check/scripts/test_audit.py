#!/usr/bin/env python3
"""Exercise the audit command and its durable artifacts at the process boundary."""

from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Thread
import unittest

from test_preflight import Handler


SCRIPT = Path(__file__).with_name('audit.py')


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/plain.html'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_preflight_only_writes_report_even_when_compression_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(SCRIPT), self.url, '--preflight-only',
                                     '--output-dir', directory, '--language', 'pl'],
                                    capture_output=True, text=True, timeout=20)
            output = Path(directory)
            self.assertTrue((output / 'report.md').is_file(), result.stderr)
            summary = json.loads((output / 'audit.json').read_text())
            self.assertEqual(summary['status'], 'PREFLIGHT_ONLY')
            self.assertEqual(summary['preflight']['verdict'], 'BLOCKED')
            self.assertEqual(summary['runs'], [])
            self.assertIn(self.url, (output / 'report.md').read_text())
            self.assertTrue((output / 'preflight.json').is_file())

    def test_report_review_preserves_history_and_aggregates_matching_measurements(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [sys.executable, str(SCRIPT), '--output-dir', str(root / 'review')]
            for index, milliseconds in enumerate([1000, 2000, 3000]):
                source = root / f'source-{index}.json'
                source.write_text(json.dumps({
                    'lighthouseVersion': '13.5.0', 'fetchTime': '2026-10-20T12:00:00Z',
                    'finalDisplayedUrl': 'https://example.com/',
                    'configSettings': {'formFactor': 'mobile', 'throttlingMethod': 'simulate'},
                    'categories': {'performance': {'score': 0.8}},
                    'audits': {'largest-contentful-paint': {'numericValue': milliseconds, 'numericUnit': 'millisecond'}},
                }))
                command += ['--report', str(source)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / 'review/audit.json').read_text())
            self.assertEqual(report['status'], 'REPORT_REVIEW')
            self.assertNotIn('preflight', report)
            self.assertEqual(report['summary']['metrics']['largest-contentful-paint']['median'], 2000)
            self.assertEqual(report['summary']['metrics']['largest-contentful-paint']['min'], 1000)
            self.assertEqual(report['summary']['metrics']['largest-contentful-paint']['max'], 3000)
            self.assertIn('2026-10-20T12:00:00Z', (root / 'review/report.md').read_text())
            self.assertTrue((root / 'review/lighthouse-1.json').is_file())

    def test_missing_node_preserves_preflight_and_an_explained_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            (bin_dir / 'curl').symlink_to(shutil.which('curl'))
            environment = {**os.environ, 'PATH': str(bin_dir)}
            result = subprocess.run([sys.executable, str(SCRIPT), self.url,
                                     '--output-dir', str(root / 'audit')], env=environment,
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads((root / 'audit/audit.json').read_text())
            self.assertEqual(report['status'], 'INCOMPLETE')
            self.assertEqual(report['preflight']['verdict'], 'BLOCKED')
            self.assertTrue(any('node' in error.lower() for error in report['errors']))
            self.assertTrue((root / 'audit/report.md').is_file())

    def test_html_review_does_not_execute_scripts_and_mismatched_reports_are_not_aggregated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = []
            for device, value in [('mobile', 1000), ('desktop', 9000)]:
                source = root / f'{device}.html'
                source.write_text('<script>throw new Error("must not execute");</script>'
                                  '<script>window.__LIGHTHOUSE_JSON__ = ' + json.dumps({
                                      'lighthouseVersion': '13.5.0', 'fetchTime': '2026-10-20T12:00:00Z',
                                      'finalDisplayedUrl': 'https://example.com/',
                                      'configSettings': {'formFactor': device},
                                      'categories': {'performance': {'score': 0.8}},
                                      'audits': {'largest-contentful-paint': {'numericValue': value, 'numericUnit': 'millisecond'}},
                                  }) + ';</script>')
                sources += ['--report', str(source)]
            result = subprocess.run([sys.executable, str(SCRIPT), *sources,
                                     '--output-dir', str(root / 'review')],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / 'review/audit.json').read_text())
            self.assertFalse(report['summary']['comparable'])
            self.assertEqual(report['summary']['metrics'], {})
            self.assertEqual(len(report['runs']), 2)

    def test_unavailable_document_stops_before_lighthouse_and_still_writes_report(self):
        with tempfile.TemporaryDirectory() as directory:
            url = f'http://127.0.0.1:{self.server.server_port}/missing.js'
            result = subprocess.run([sys.executable, str(SCRIPT), url, '--no-install',
                                     '--output-dir', directory],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads((Path(directory) / 'audit.json').read_text())
            self.assertEqual(report['runs'], [])
            self.assertNotIn('tools', report)
            self.assertFalse(report['preflight']['http_document_available'])
            self.assertTrue((Path(directory) / 'report.md').is_file())

    def test_malformed_report_still_produces_an_incomplete_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'broken.json'
            source.write_text('{broken JSON')
            result = subprocess.run([sys.executable, str(SCRIPT), '--report', str(source),
                                     '--output-dir', str(root / 'review')],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads((root / 'review/audit.json').read_text())
            self.assertEqual(report['status'], 'INCOMPLETE')
            self.assertTrue(report['errors'])
            self.assertTrue((root / 'review/report.md').is_file())

    def test_import_never_overwrites_reports_in_the_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = []
            for index, value in enumerate([1000, 3000], 1):
                source = root / f'lighthouse-{index}.json'
                source.write_text(json.dumps({
                    'lighthouseVersion': '13.5.0', 'finalDisplayedUrl': 'https://example.com/',
                    'audits': {'largest-contentful-paint': {'numericValue': value, 'numericUnit': 'millisecond'}},
                }))
                sources.append(source)
            original = [source.read_bytes() for source in sources]
            result = subprocess.run([sys.executable, str(SCRIPT), '--report', str(sources[1]),
                                     '--report', str(sources[0]), '--output-dir', directory],
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual([source.read_bytes() for source in sources], original)

    def test_invalid_report_fields_produce_an_incomplete_markdown_report(self):
        for field in [{'runWarnings': None}, {'numericUnit': []}]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                lhr = {'lighthouseVersion': '13.5.0', 'finalDisplayedUrl': 'https://example.com/',
                       'audits': {'largest-contentful-paint': {'numericValue': 1000, 'numericUnit': 'millisecond'}}}
                if 'runWarnings' in field:
                    lhr.update(field)
                else:
                    lhr['audits']['largest-contentful-paint'].update(field)
                source = root / 'source.json'
                source.write_text(json.dumps(lhr))
                result = subprocess.run([sys.executable, str(SCRIPT), '--report', str(source),
                                         '--output-dir', str(root / 'review')],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 2, result.stderr)
                report = json.loads((root / 'review/audit.json').read_text())
                self.assertEqual(report['status'], 'INCOMPLETE')
                self.assertTrue(report['errors'])
                self.assertTrue((root / 'review/report.md').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
