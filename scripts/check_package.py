#!/usr/bin/env python3
"""Check this skill's required files and local Markdown links using stdlib only.

This is not a YAML parser, a visual evaluator, or the official skill validator.
"""

import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


REQUIRED = (
    'SKILL.md', 'agents/openai.yaml', 'references/workflow.md',
    'references/character-system.md', 'references/quality.md',
    'references/project-record.md',
)


def check(root):
    root = Path(root).resolve()
    errors = []
    for name in REQUIRED:
        path = root / name
        if not path.is_file():
            errors.append(f'Missing required file: {name}')
        elif path.stat().st_size == 0:
            errors.append(f'Empty required file: {name}')

    for path in sorted(root.rglob('*.md')):
        try:
            content = path.read_text(encoding='utf-8-sig')
        except UnicodeError:
            errors.append(f'Not UTF-8: {path.relative_to(root)}')
            continue
        # This package uses inline links; fenced examples are not references.
        content = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', content,
                         flags=re.MULTILINE | re.DOTALL)
        for target in re.findall(r'\]\(([^\s)]+)\)', content):
            url = urlsplit(target.strip('<>'))
            if url.scheme or url.netloc or not url.path:
                continue
            resolved = (path.parent / unquote(url.path)).resolve()
            if not resolved.is_relative_to(root):
                errors.append(f'Link outside package: {path.relative_to(root)} -> {target}')
            elif not resolved.is_file():
                errors.append(f'Broken link: {path.relative_to(root)} -> {target}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('PASS: required files and local inline Markdown links.')
    print('Not checked: YAML syntax, remote URLs, visual quality, installation.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
