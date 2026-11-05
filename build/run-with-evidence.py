#!/usr/bin/env python3
"""Run a check and retain its exact output, identity and screenshots, including failures.

Reports are test evidence, not screenshots of a running operating system.
No shell interpolation is used. Execute only commands whose output is safe to share.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def source_digest():
    paths = subprocess.check_output(
        ['git', '-C', str(ROOT), 'ls-files', '-z', '--cached', '--others', '--exclude-standard']
    ).split(b'\0')
    digest = hashlib.sha256()
    for raw in sorted(set(p for p in paths if p)):
        path = ROOT / os.fsdecode(raw)
        digest.update(raw + b'\0')
        if path.is_symlink():
            digest.update(b'link\0' + os.fsencode(os.readlink(path)))
        elif path.is_file():
            digest.update(str(path.stat().st_mode & 0o777).encode() + b'\0')
            digest.update(path.read_bytes())
        else:
            digest.update(b'deleted')
        digest.update(b'\0')
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--kind', choices=['source', 'package-container', 'browser-preview', 'vm', 'hardware'], required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout < 1:
        parser.error('a command and positive timeout are required')
    output = Path(args.output).resolve()
    # Never overwrite an earlier run, including its failure evidence.
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc)
    record = {
        'schema_version': 1, 'name': args.name, 'kind': args.kind,
        'started_at': started.isoformat(), 'commit': git('rev-parse', 'HEAD'),
        'source_digest': source_digest(), 'working_tree': git('status', '--short'),
        'command': command, 'host': os.uname().sysname + ' ' + os.uname().machine,
        'installation_approved': False,
        'run_url': (f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                    if os.environ.get('GITHUB_RUN_ID') and os.environ.get('GITHUB_REPOSITORY') else None),
    }
    log = output / 'output.log'
    before = time.monotonic()
    with log.open('wb') as stream:
        try:
            process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True,
                                       env={**os.environ, 'OREZ_EVIDENCE_DIR': str(output)})
            try:
                result = process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                stream.write(b'\nEVIDENCE RUNNER: command exceeded the configured timeout.\n')
                result = 124
        except OSError as error:
            stream.write(f'Unable to start command: {error}\n'.encode())
            result = 127
    record.update(exit_code=result, status='passed' if result == 0 else 'failed',
                  duration_seconds=round(time.monotonic() - before, 2),
                  finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    # Captures all log pages, even when the underlying check failed.
    render = subprocess.run(['node', str(ROOT / 'build/render-evidence.mjs'), str(output)], cwd=ROOT)
    print(log.read_text(errors='replace'))
    print(f"Evidence: {output}; check={record['status']}; screenshots={'captured' if render.returncode == 0 else 'FAILED'}")
    return result if result != 0 else render.returncode


if __name__ == '__main__':
    sys.exit(main())
