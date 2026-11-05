#!/usr/bin/env python3
"""Copy into a NEW build directory with explicit desktop payload permissions.

Never chmod the checkout, an installed root, or symlink targets. A restrictive
checkout umask must not produce unreadable launchers or untraversable /usr.
"""
import argparse
from pathlib import Path, PurePosixPath
import shutil


def stage(source, output, manifest=None):
    source, output = Path(source), Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError('staging output must not already exist')
    if manifest is None:
        shutil.copytree(source, output, symlinks=True)
    else:
        entries = [line.strip() for line in Path(manifest).read_text().splitlines()
                   if line.strip() and not line.lstrip().startswith('#')]
        if not entries or len(entries) != len(set(entries)):
            raise ValueError('empty or duplicate manifest')
        for relative in entries:
            if relative.startswith('/') or '..' in PurePosixPath(relative).parts or '\\' in relative:
                raise ValueError('unsafe manifest path')
            item = source / relative
            if not item.is_file() or item.is_symlink() or source.resolve() not in item.resolve().parents:
                raise ValueError('missing or escaping payload source: ' + relative)
        output.mkdir()
        for relative in entries:
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, target)
    for item in [output, *output.rglob('*')]:
        if item.is_symlink():
            continue
        relative = item.relative_to(output).as_posix()
        executable = relative.startswith('usr/bin/') or (
            relative.startswith('etc/xdg/plasma-workspace/env/') and relative.endswith('.sh'))
        item.chmod(0o755 if item.is_dir() or executable else 0o644)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--manifest', type=Path)
    a = p.parse_args()
    stage(a.source, a.output, a.manifest)
