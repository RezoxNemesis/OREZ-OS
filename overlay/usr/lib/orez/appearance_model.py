#!/usr/bin/env python3
"""OREZ Appearance: a small, fixed set of choices mapped to native KDE commands.

No shell strings and no user-supplied text reaches a command line: every
command is an argument list built from constants below or from values read
back from KDE and validated against strict patterns before reuse.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

WALLPAPERS = Path('/usr/share/wallpapers')
PREVIEWS = Path('/usr/share/orez/appearance/previews')
STATE = Path.home() / '.config' / 'orez-appearance.json'


@dataclass(frozen=True)
class Option:
    id: str
    title: str
    summary: str


GROUPS: dict[str, tuple[str, list[Option]]] = {
    'layout': ('Layout', [
        Option('familiar', 'Familiar', 'Full-width taskbar at the bottom with a Start menu, like Windows.'),
        Option('dock', 'Dock', 'Compact floating dock centred at the bottom, like macOS.'),
    ]),
    'theme': ('Colours', [
        Option('OREZPaper', 'Paper', 'Warm paper white with ink-black text. Calm and bright.'),
        Option('OREZInk', 'Ink', 'Deep ink background with paper-white text. Easy on the eyes at night.'),
    ]),
    'wallpaper': ('Wallpaper', [
        Option('OREZ-Rest', 'Rest', 'The wanderer resting beneath the blossom tree.'),
        Option('OREZ-Horizon', 'Horizon', 'The wanderer facing the lake and mountains.'),
    ]),
    'effects': ('Effects', [
        Option('calm', 'Calm glass', 'Frosted blur and smooth, short animations.'),
        Option('light', 'Light', 'No blur and quicker animations. Best for older hardware.'),
        Option('still', 'Still', 'No animations at all. Also helps with motion sensitivity.'),
    ]),
    'performance': ('Performance', [
        Option('balanced', 'Balanced', 'Good speed with sensible power use. Recommended.'),
        Option('performance', 'Performance', 'Maximum CPU speed for games and heavy work; uses more power.'),
        Option('power-saver', 'Quiet', 'Lower power and fan noise.'),
    ]),
}

LAYOUT_SCRIPTS = {
    'familiar': ('panels().forEach(function(p){p.location="bottom";p.alignment="center";'
                 'p.lengthMode="fill";p.floating=false;p.height=Math.round(gridUnit*2.4);});'),
    'dock': ('panels().forEach(function(p){p.location="bottom";p.alignment="center";'
             'p.lengthMode="fit";p.floating=true;p.height=Math.round(gridUnit*3);});'),
}
READ_LAYOUT = ('print(JSON.stringify(panels().map(function(p){return {location:p.location,'
               'alignment:p.alignment,lengthMode:p.lengthMode,floating:p.floating,height:p.height};})));')
EFFECTS = {  # (blur enabled, animation duration factor)
    'calm': ('true', '1'),
    'light': ('false', '0.5'),
    'still': ('false', '0'),
}
_ENUM = {'location': {'top', 'bottom', 'left', 'right', 'floating'},
         'alignment': {'left', 'center', 'right'}, 'lengthMode': {'fill', 'fit', 'custom'}}


def option_ids(group: str) -> set[str]:
    return {o.id for o in GROUPS[group][1]}


def plasma_script(script: str) -> list[str]:
    return ['qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', script]


def plan(group: str, choice: str) -> list[list[str]]:
    """Exact commands that apply one choice. Raises on anything not offered."""
    if choice not in option_ids(group):
        raise ValueError('Unknown appearance choice')
    if group == 'layout':
        return [plasma_script(LAYOUT_SCRIPTS[choice])]
    if group == 'theme':
        return [['plasma-apply-colorscheme', choice]]
    if group == 'wallpaper':
        return [['plasma-apply-wallpaperimage', str(WALLPAPERS / choice)]]
    if group == 'effects':
        blur, factor = EFFECTS[choice]
        return [['kwriteconfig6', '--file', 'kwinrc', '--group', 'Plugins', '--key', 'blurEnabled', blur],
                ['kwriteconfig6', '--file', 'kdeglobals', '--group', 'KDE', '--key', 'AnimationDurationFactor', factor],
                ['qdbus6', 'org.kde.KWin', '/KWin', 'reconfigure']]
    if group == 'performance':
        return [['powerprofilesctl', 'set', choice]]
    raise ValueError('Unknown appearance group')


def restore_layout_script(saved_json: str) -> str:
    """Rebuild a layout restore script from validated, previously read values."""
    panels = json.loads(saved_json)
    if not isinstance(panels, list) or len(panels) > 8:
        raise ValueError('Unexpected panel state')
    parts = []
    for i, p in enumerate(panels):
        if not all(p.get(k) in allowed for k, allowed in _ENUM.items()):
            raise ValueError('Unexpected panel value')
        if not isinstance(p.get('floating'), bool) or not isinstance(p.get('height'), int) or not 16 <= p['height'] <= 200:
            raise ValueError('Unexpected panel geometry')
        parts.append('if(panels()[%d]){var p=panels()[%d];p.location="%s";p.alignment="%s";p.lengthMode="%s";'
                     'p.floating=%s;p.height=%d;}' % (i, i, p['location'], p['alignment'], p['lengthMode'],
                                                     'true' if p['floating'] else 'false', p['height']))
    return ''.join(parts)


def _read(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def snapshot(group: str) -> list[list[str]]:
    """Commands that return the desktop to its current state for this group."""
    if group == 'layout':
        saved = _read(plasma_script(READ_LAYOUT))
        try:
            return [plasma_script(restore_layout_script(saved))] if saved else []
        except (ValueError, json.JSONDecodeError):
            return []
    if group == 'theme':
        current = _read(['kreadconfig6', '--file', 'kdeglobals', '--group', 'General', '--key', 'ColorScheme'])
        return [['plasma-apply-colorscheme', current]] if re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', current) else []
    if group == 'wallpaper':
        current = load_state().get('wallpaper')
        return plan('wallpaper', current) if current in option_ids('wallpaper') else []
    if group == 'effects':
        blur = _read(['kreadconfig6', '--file', 'kwinrc', '--group', 'Plugins', '--key', 'blurEnabled', '--default', 'true'])
        factor = _read(['kreadconfig6', '--file', 'kdeglobals', '--group', 'KDE', '--key', 'AnimationDurationFactor', '--default', '1'])
        if blur not in {'true', 'false'} or not re.fullmatch(r'\d{1,2}(\.\d{1,3})?', factor):
            return []
        return [['kwriteconfig6', '--file', 'kwinrc', '--group', 'Plugins', '--key', 'blurEnabled', blur],
                ['kwriteconfig6', '--file', 'kdeglobals', '--group', 'KDE', '--key', 'AnimationDurationFactor', factor],
                ['qdbus6', 'org.kde.KWin', '/KWin', 'reconfigure']]
    if group == 'performance':
        current = _read(['powerprofilesctl', 'get'])
        return plan('performance', current) if current in option_ids('performance') else []
    return []


def run(commands: list[list[str]]) -> list[str]:
    errors = []
    for cmd in commands:
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=True)
        except FileNotFoundError:
            errors.append(cmd[0] + ' is not installed')
        except subprocess.CalledProcessError as e:
            errors.append(cmd[0] + ': ' + (e.stderr or '').strip()[:200])
        except subprocess.TimeoutExpired:
            errors.append(cmd[0] + ' did not respond')
    return errors


def load_state() -> dict:
    try:
        data = json.loads(STATE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_choice(group: str, choice: str) -> None:
    if choice not in option_ids(group):
        raise ValueError('Unknown appearance choice')
    data = load_state(); data[group] = choice
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2) + '\n')


def preview_image(group: str, choice: str) -> Path | None:
    if choice not in option_ids(group):
        return None
    if group == 'wallpaper':
        images = sorted((WALLPAPERS / choice / 'contents' / 'images').glob('*.jpg'))
        return images[-1] if images else None
    captured = PREVIEWS / f'{group}-{choice}.png'
    return captured if captured.is_file() else None
