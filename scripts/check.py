#!/usr/bin/env python3
"""Validate the published catalog and run its bundled Python contract tests."""

import ast
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]


def validate_catalog(root):
    errors = []
    license_path = root / 'LICENSE'
    license_text = license_path.read_bytes() if license_path.is_file() else b''
    if not license_text.strip():
        errors.append('LICENSE: missing or empty distribution license')
    skills = sorted((root / 'skills').rglob('SKILL.md'))
    if not skills:
        return errors + ['No published skills found under skills/.']
    readme = (root / 'README.md').read_text(encoding='utf-8')
    names = set()
    for entry in skills:
        label = entry.relative_to(root).as_posix()
        bundled_license = entry.parent / 'LICENSE'
        if not bundled_license.is_file():
            errors.append(f'{label}: missing bundled LICENSE')
        elif license_text and bundled_license.read_bytes() != license_text:
            errors.append(f'{label}: bundled LICENSE must match the root LICENSE')
        content = entry.read_text(encoding='utf-8')
        match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', content, re.DOTALL)
        if not match:
            errors.append(f'{label}: missing YAML frontmatter')
            continue
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            errors.append(f'{label}: invalid YAML: {exc}')
            continue
        if not isinstance(data, dict):
            errors.append(f'{label}: frontmatter must be a mapping')
            continue
        name = data.get('name')
        if not isinstance(name, str) or len(name) > 64 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            errors.append(f'{label}: name must be lowercase hyphenated text, at most 64 characters')
        elif name != entry.parent.name:
            errors.append(f'{label}: name must match its containing directory')
        if isinstance(name, str):
            if name in names:
                errors.append(f'{label}: duplicate skill name {name}')
            names.add(name)
        description = data.get('description')
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            errors.append(f'{label}: description must contain 1 to 1024 characters')
        if not content[match.end():].strip():
            errors.append(f'{label}: missing skill instructions')
        if f']({label})' not in readme:
            errors.append(f'{label}: missing catalog link in README.md')
        for target in re.findall(r'\[[^\]\n]*\]\(([^\s)]+)\)', content):
            url = urlsplit(target.strip('<>'))
            if url.scheme or url.netloc or not url.path:
                continue
            local = (entry.parent / unquote(url.path)).resolve()
            if not local.is_relative_to(entry.parent.resolve()) or not local.exists():
                errors.append(f'{label}: missing or non-bundled resource {target}')
        metadata = entry.parent / 'agents/openai.yaml'
        if metadata.exists():
            try:
                ui = yaml.safe_load(metadata.read_text(encoding='utf-8'))
                if not isinstance(ui, dict):
                    errors.append(f'{label}: agents/openai.yaml must be a mapping')
            except yaml.YAMLError as exc:
                errors.append(f'{label}: invalid agents/openai.yaml: {exc}')
        for script in sorted((entry.parent / 'scripts').rglob('*.py')):
            try:
                ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
            except (SyntaxError, UnicodeError) as exc:
                errors.append(f'{script.relative_to(root)}: {exc}')
    return errors


def main():
    errors = validate_catalog(ROOT)
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print('Published skill catalog is valid.', flush=True)
    tests = sorted((ROOT / 'scripts').glob('test_*.py')) + sorted((ROOT / 'skills').rglob('test_*.py'))
    for test in tests:
        print(f'Running {test.relative_to(ROOT)}', flush=True)
        result = subprocess.run([sys.executable, str(test)], cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
