# -*- coding: utf-8 -*-
"""Install Atomize into the desktop's application and icon databases.

    python3 icons/install_desktop.py              # into ~/.local/share
    python3 icons/install_desktop.py --system     # into /usr/share  (needs root)
    python3 icons/install_desktop.py --uninstall

Why this exists
---------------
Without an entry in the icon theme the shell has nothing to look up by name, so
it falls back to the raster the process publishes over ``_NET_WM_ICON`` and
rescales that to whatever the panel needs. An ICO cannot help past 256 px - the
format stores each entry's width in a single byte - so on a scaled display the
result is an upscale. Installing the scalable SVG plus the standard PNG sizes
lets the shell render the mark at exactly the size it wants.

Everything is resolved at run time from ``XDG_DATA_HOME`` and from whichever
launcher is actually on PATH, so the same command works on any machine.
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STAGE = os.path.join(HERE, 'desktop')
ICON_NAME = 'atomize'
ENTRY_NAME = ICON_NAME + '.desktop'


def data_dir(system):
    if system:
        return '/usr/share'
    return os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')


def launcher():
    """Prefer the installed console script; fall back to the module form."""
    exe = shutil.which('atomize-itc') or shutil.which('atomize')
    if exe:
        return exe
    return '%s -m atomize' % (shutil.which('python3') or sys.executable)


def _walk(top):
    for base, _dirs, files in os.walk(top):
        for f in files:
            full = os.path.join(base, f)
            yield full, os.path.relpath(full, top)


def install(system):
    if not os.path.isdir(STAGE):
        raise SystemExit('missing %s - run: python3 icons/make_icons.py' % STAGE)
    root = data_dir(system)
    icons_src = os.path.join(STAGE, 'hicolor')
    icons_dst = os.path.join(root, 'icons', 'hicolor')
    n = 0
    for full, rel in _walk(icons_src):
        dst = os.path.join(icons_dst, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(full, dst)
        n += 1
    print('installed %d icon files into %s' % (n, icons_dst))

    apps = os.path.join(root, 'applications')
    os.makedirs(apps, exist_ok=True)
    entries = sorted(f for f in os.listdir(STAGE) if f.endswith('.desktop'))
    for name in entries:
        with open(os.path.join(STAGE, name)) as fh:
            entry = fh.read()
        entry = entry.replace('Exec=atomize-itc', 'Exec=' + launcher())
        dst = os.path.join(apps, name)
        with open(dst, 'w') as fh:
            fh.write(entry)
        os.chmod(dst, 0o755)
    print('installed %d desktop entries into %s  (Exec=%s)'
          % (len(entries), apps, launcher()))
    refresh(root)


def uninstall(system):
    root = data_dir(system)
    removed = 0
    icons_dst = os.path.join(root, 'icons', 'hicolor')
    for full, rel in _walk(os.path.join(STAGE, 'hicolor')):
        dst = os.path.join(icons_dst, rel)
        if os.path.isfile(dst):
            os.remove(dst)
            removed += 1
    for name in sorted(f for f in os.listdir(STAGE) if f.endswith('.desktop')):
        entry = os.path.join(root, 'applications', name)
        if os.path.isfile(entry):
            os.remove(entry)
            removed += 1
    print('removed %d files from %s' % (removed, root))
    refresh(root)


def refresh(root):
    """Nudge the caches if the tools are present; harmless when they are not."""
    for cmd in (['update-desktop-database', os.path.join(root, 'applications')],
                ['gtk-update-icon-cache', '-f', '-t',
                 os.path.join(root, 'icons', 'hicolor')]):
        if shutil.which(cmd[0]) is None:
            continue
        try:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except OSError:
            pass


def main():
    if not sys.platform.startswith('linux'):
        raise SystemExit('nothing to do: desktop entries and icon themes are a '
                         'freedesktop concept. Windows takes its taskbar icon '
                         'from the window itself (see set_app_user_model_id in '
                         'gui_style.py), so the .ico files are all it needs.')
    args = sys.argv[1:]
    system = '--system' in args
    if '--uninstall' in args:
        uninstall(system)
    else:
        install(system)


if __name__ == '__main__':
    main()
