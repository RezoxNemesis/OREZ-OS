"""Actual native applications and failure paths in a disposable ordinary-user account.

No hardware, system backup, distro boot or gaming compatibility is inferred.
"""
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time

assert os.getuid() != 0 and Path('/.dockerenv').exists()
EVIDENCE = Path('/evidence')
ROOT = Path(tempfile.mkdtemp(prefix='orez-capabilities-', dir=Path.home()))
results = []


def run(*args, timeout=60, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, timeout=timeout, **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scenario(name, function):
    before = time.monotonic()
    try:
        detail = function()
        record = {'scenario': name, 'status': 'passed', 'detail': detail}
    except Exception as error:
        record = {'scenario': name, 'status': 'failed', 'detail': str(error)}
        if isinstance(error, subprocess.CalledProcessError):
            record['stdout'] = error.stdout
            record['stderr'] = error.stderr
    record['seconds'] = round(time.monotonic() - before, 3)
    results.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)


def files():
    source = ROOT / '日本語 — project with spaces.txt'
    source.write_text('OREZ\n日本語\n' * 5000)
    copied = ROOT / 'копия.txt'
    shutil.copy2(source, copied)
    assert digest(source) == digest(copied)
    moved = copied.rename(ROOT / 'renamed.txt')
    assert moved.exists() and not copied.exists()
    link = ROOT / 'user-link'
    link.symlink_to(source)
    assert link.read_bytes() == source.read_bytes()
    return 'Unicode/space filenames, copy checksum, rename and user symlink succeeded'


def archive():
    source = ROOT / 'archive-source'
    source.mkdir()
    (source / 'project.txt').write_text('recover this user data')
    archive_file = ROOT / 'backup.tar.gz'
    run('tar', '-czf', str(archive_file), '-C', str(source), '.')
    target = ROOT / 'archive-restored'
    target.mkdir()
    run('tar', '-xzf', str(archive_file), '-C', str(target))
    assert digest(source / 'project.txt') == digest(target / 'project.txt')
    return 'tar user-file round trip; not a Snapper/Restic or system recovery test'


def compile_cpp():
    source = ROOT / 'main.cpp'
    source.write_text('#include <iostream>\n#include <numeric>\n#include <vector>\nint main(){std::vector<int> v(1000);std::iota(v.begin(),v.end(),1);std::cout<<std::accumulate(v.begin(),v.end(),0)<<"\\n";}\n')
    binary = ROOT / 'compiled-program'
    run('g++', '-std=c++20', '-O2', str(source), '-o', str(binary))
    assert run(str(binary)).stdout.strip() == '500500'
    return 'Actual C++20 compile and execution returned the expected result'


def git_recovery():
    project = ROOT / 'git-project'
    project.mkdir()
    run('git', 'init', cwd=project)
    run('git', 'config', 'user.name', 'OREZ QA fixture', cwd=project)
    run('git', 'config', 'user.email', 'qa@invalid.example', cwd=project)
    target = project / 'example.txt'
    target.write_text('version one')
    run('git', 'add', '.', cwd=project)
    run('git', '-c', 'commit.gpgsign=false', 'commit', '-m', 'Disposable fixture', cwd=project)
    target.write_text('accidental edit')
    run('git', 'restore', 'example.txt', cwd=project)
    assert target.read_text() == 'version one'
    return 'Offline Git commit and restoration in a disposable repository'


def database():
    db = sqlite3.connect(ROOT / 'transactions.sqlite')
    db.execute('create table work (id integer primary key, name text)')
    db.execute('insert into work(name) values (?)', ('saved',))
    db.commit()
    db.execute('insert into work(name) values (?)', ('should roll back',))
    db.rollback()
    assert db.execute('select name from work').fetchall() == [('saved',)]
    db.close()
    return 'SQLite commit, rollback and data retention verified'


def privilege():
    denied = Path('/etc/orez-qa-must-not-exist')
    assert not denied.exists()
    try:
        denied.write_text('must not succeed')
    except PermissionError:
        pass
    else:
        raise AssertionError('ordinary user unexpectedly wrote /etc')
    result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, text=True, timeout=5)
    assert result.returncode != 0
    assert not denied.exists()
    return 'Ordinary-user /etc write and passwordless sudo denied; not a general security audit'


def full_filesystem():
    scratch = Path('/scratch')
    stats = os.statvfs(scratch)
    assert stats.f_blocks * stats.f_frsize <= 20 * 1024 * 1024, 'Only bounded test tmpfs may be filled'
    sentinel = scratch / 'preserve.txt'
    sentinel.write_text('unrelated data')
    expected = digest(sentinel)
    fill = scratch / 'fill.bin'
    try:
        with fill.open('wb') as file:
            for _ in range(25):
                file.write(b'x' * 1024 * 1024)
        raise AssertionError('expected ENOSPC did not occur')
    except OSError as error:
        assert error.errno == errno.ENOSPC
    finally:
        fill.unlink(missing_ok=True)
    assert digest(sentinel) == expected
    (scratch / 'after.txt').write_text('writes work after cleanup')
    return 'Real ENOSPC on private 16 MiB tmpfs; unrelated data retained; writes recover after cleanup'


def memory_limit():
    code = '''import resource
resource.setrlimit(resource.RLIMIT_AS, (128*1024*1024, 128*1024*1024))
try:
    value = bytearray(512*1024*1024)
except MemoryError:
    print('handled allocation failure')
else:
    raise SystemExit(1)
'''
    assert run('python3', '-c', code).stdout.strip() == 'handled allocation failure'
    return 'MemoryError handled in a capped Python process; not desktop OOM recovery'


def video():
    output = ROOT / 'test-video.mp4'
    result = run('ffmpeg', '-hide_banner', '-nostdin', '-y', '-f', 'lavfi', '-i', 'testsrc=size=320x180:rate=12',
                 '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '1', '-c:v', 'libx264',
                 '-threads', '1', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(output))
    (EVIDENCE / 'ffmpeg.log').write_text(result.stderr)
    streams = json.loads(run('ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(output)).stdout)['streams']
    assert {s['codec_type'] for s in streams} == {'video', 'audio'}
    run('ffmpeg', '-hide_banner', '-nostdin', '-y', '-i', str(output), '-frames:v', '1', str(EVIDENCE / 'video-decoded-frame.png'))
    (EVIDENCE / 'media-streams.json').write_text(json.dumps(streams, indent=2))
    return 'CPU H.264/AAC encode, probe and frame decode; no speaker, microphone, GPU encoder or editing-app qualification'


def blender():
    script = ROOT / 'render.py'
    script.write_text("""import bpy
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=4
scene.render.resolution_x=320
scene.render.resolution_y=180
scene.render.resolution_percentage=100
scene.render.filepath='/evidence/blender-cpu-render.png'
bpy.ops.render.render(write_still=True)
""")
    output = run('blender', '--background', '--factory-startup', '--threads', '2', '--python', str(script), timeout=120)
    (EVIDENCE / 'blender.log').write_text(output.stdout + output.stderr)
    assert (EVIDENCE / 'blender-cpu-render.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    return 'Actual Blender Cycles CPU render, 320×180, four samples; no RTX/CUDA/OptiX claim'


def software_graphics():
    output = run('glxinfo', '-B').stdout
    (EVIDENCE / 'glxinfo.txt').write_text(output)
    assert 'llvmpipe' in output.lower() or 'softpipe' in output.lower()
    log = (EVIDENCE / 'glxgears.log').open('w')
    app = subprocess.Popen(['glxgears', '-info'], stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(20):
            found = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '^glxgears$'], capture_output=True)
            if found.returncode == 0:
                break
            assert app.poll() is None
            time.sleep(.25)
        (EVIDENCE / 'x11-window-tree.txt').write_text(run('xwininfo', '-root', '-tree').stdout)
        assert found.returncode == 0, 'glxgears window not found by its title'
        time.sleep(1)
        run('scrot', str(EVIDENCE / 'software-opengl.png'))
    finally:
        subprocess.run(['scrot', str(EVIDENCE / 'opengl-final-frame.png')], capture_output=True)
        app.terminate()
        app.wait(timeout=5)
        log.close()
    return 'Actual software OpenGL window; not GPU performance or game compatibility'


for name, function in [
    ('file names/copy/rename/symlink', files), ('user-file archive restore', archive),
    ('C++ compilation/execution', compile_cpp), ('offline Git restore', git_recovery),
    ('SQLite transaction rollback', database), ('ordinary-user privilege boundary', privilege),
    ('full-filesystem failure and recovery', full_filesystem), ('bounded-memory failure', memory_limit),
    ('audio/video encoding and decoding', video), ('Blender CPU rendering', blender),
    ('software OpenGL rendering', software_graphics),
]:
    if not os.environ.get('OREZ_CAPABILITY_FILTER') or os.environ['OREZ_CAPABILITY_FILTER'] in name:
        scenario(name, function)
(EVIDENCE / 'capabilities.json').write_text(json.dumps({'environment': 'ordinary user in isolated Ubuntu container', 'installation_approved': False, 'scenarios': results}, indent=2))
shutil.rmtree(ROOT)
raise SystemExit(any(r['status'] != 'passed' for r in results))
