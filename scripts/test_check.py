#!/usr/bin/env python3
"""Packaging regressions using the real published skill in isolated checkouts."""

from pathlib import Path
import shutil
import tempfile
import unittest

from check import ROOT, validate_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for name in ('README.md', 'LICENSE'):
            shutil.copy(ROOT / name, self.root / name)
        self.skill = self.root / 'skills/lighthouse-check'
        shutil.copytree(ROOT / 'skills/lighthouse-check', self.skill,
                        ignore=shutil.ignore_patterns('__pycache__'))

    def test_complete_package_passes(self):
        self.assertEqual(validate_catalog(self.root), [])

    def test_removing_scripts_cannot_leave_a_green_catalog(self):
        shutil.rmtree(self.skill / 'scripts')
        errors = validate_catalog(self.root)
        for name in ('preflight.py', 'test_preflight.py'):
            self.assertTrue(any(name in error for error in errors), errors)

    def test_license_must_travel_with_the_skill(self):
        (self.skill / 'LICENSE').unlink()
        self.assertTrue(any('missing bundled LICENSE' in error
                            for error in validate_catalog(self.root)))

    def test_bundled_license_cannot_drift(self):
        (self.skill / 'LICENSE').write_text('Different license\n', encoding='utf-8')
        self.assertTrue(any('must match the root LICENSE' in error
                            for error in validate_catalog(self.root)))

    def test_root_license_is_required(self):
        (self.root / 'LICENSE').unlink()
        self.assertIn('LICENSE: missing or empty distribution license',
                      validate_catalog(self.root))


if __name__ == '__main__':
    unittest.main(verbosity=2)
