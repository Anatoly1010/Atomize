# -*- coding: utf-8 -*-
"""Rasterise the SVG icon sources into the files Atomize actually loads.

Run from anywhere:

    python3 icons/make_icons.py            # write every target
    python3 icons/make_icons.py --check    # report what would change, write nothing

Window icons are emitted as multi-size ``.ico`` rather than a single large PNG:
Qt then picks the entry matching the requested size instead of smooth-scaling one
bitmap down to 16 px, which is what made the previous 500x500 PNGs look soft in
title bars and task bars.

Only PyQt6 is needed - it is already a runtime dependency, and the ICO container
is written here directly so nothing extra is required to build the icons.
"""

import os
import re
import struct
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QRectF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SVG = os.path.join(HERE, 'svg')

# ICO entries cannot exceed 256 px: the directory record stores width in one
# byte, with 0 meaning 256. Anything larger has to reach the desktop through the
# icon theme instead, which is what DESKTOP_SIZES below is for.
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)

# what a freedesktop icon theme is expected to carry, plus the scalable SVG
DESKTOP_SIZES = (16, 22, 24, 32, 36, 48, 64, 72, 96, 128, 192, 256, 512)

GUI = 'atomize/control_center/gui'
CC = 'atomize/control_center'

# Which tool icons to build is not hard-coded: the control-centre sources are
# scanned for the files they load. Every fork carries a different subset of the
# tools, so this keeps one identical script across all of them - a fork gets
# exactly the icons it asks for, and a typo'd name fails loudly instead of
# silently leaving a window without an icon.
ICON_REF = re.compile(r"\b(icon_[a-z0-9_]+)\.ico\b")


def tool_icons():
    """Icon names referenced by this repo's control-centre sources."""
    names = set()
    src_dir = os.path.join(ROOT, CC)
    if not os.path.isdir(src_dir):
        return names
    for f in sorted(os.listdir(src_dir)):
        if not f.endswith('.py'):
            continue
        with open(os.path.join(src_dir, f), encoding='utf-8') as fh:
            names.update(ICON_REF.findall(fh.read()))
    return names


def ico_targets():
    targets = {'icon_atomize': 'atomize/main/icon.ico'}
    for name in sorted(tool_icons()):
        if not os.path.isfile(os.path.join(SVG, name + '.svg')):
            raise SystemExit('%s is loaded by a tool but icons/svg/%s.svg is '
                             'missing' % (name, name))
        targets[name] = '%s/%s.ico' % (GUI, name)
    return targets

# svg source -> (target, width, height) for the flat images
PNG_TARGETS = [
    ('icon_atomize', 'atomize/main/Icon.png', 500, 500),
    ('logo_banner',  'screenshots/logoAtomize.png', 838, 340),
]

# staged freedesktop payload; install_desktop.py copies it into XDG_DATA_HOME
DESKTOP_DIR = 'icons/desktop'
DESKTOP_ICON_NAME = 'atomize'

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Version=1.0
Name=Atomize
GenericName=Spectrometer control
Comment=Modular instrument control for spectrometers
Exec=__EXEC__ %f
Icon=atomize
Terminal=false
Categories=Science;Physics;
Keywords=EPR;spectrometer;instrument;liveplot;
StartupNotify=true
StartupWMClass=Atomize
"""

# Each control-centre tool is its own process, so the shell treats it as its own
# application. Giving each one a hidden entry means its icon is resolved from
# the theme at the exact size wanted, instead of being rescaled from the raster
# the process publishes - and on Wayland, where there is no way to push a window
# icon at all, this is the only thing that puts an icon on the tool window.
TOOL_ENTRY = """[Desktop Entry]
Type=Application
Version=1.0
Name=__NAME__
Comment=Atomize control-centre tool
Exec=false
Icon=__ICON__
Terminal=false
NoDisplay=true
Categories=Science;Physics;
StartupWMClass=__WMCLASS__
"""


def render(svg_path, w, h):
    r = QSvgRenderer(svg_path)
    if not r.isValid():
        raise SystemExit('unreadable SVG: %s' % svg_path)
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    r.render(p, QRectF(0, 0, w, h))
    p.end()
    return img


def png_bytes(img):
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, 'PNG')
    buf.close()
    return bytes(ba)


def ico_bytes(svg_path, sizes=ICO_SIZES):
    """A multi-size ICO whose entries are PNG-compressed. Each size is rendered
    from the vector at that size, so nothing is ever downscaled."""
    blobs = [(s, png_bytes(render(svg_path, s, s))) for s in sizes]
    out = struct.pack('<HHH', 0, 1, len(blobs))
    offset = 6 + 16 * len(blobs)
    for s, blob in blobs:
        out += struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32,
                           len(blob), offset)
        offset += len(blob)
    for _, blob in blobs:
        out += blob
    return out


def write(path, data, check):
    old = None
    if os.path.isfile(path):
        with open(path, 'rb') as fh:
            old = fh.read()
    if old == data:
        return 'same'
    if check:
        return 'would ' + ('update' if old else 'create')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(data)
    return 'updated' if old else 'created'


def stage_desktop(check):
    """Build the freedesktop payload: a scalable SVG, a PNG at every theme size,
    and the desktop entry. A window icon alone is not enough on Linux - with no
    entry in the icon theme the shell falls back to the raster the process
    publishes over _NET_WM_ICON and rescales that, which is what makes the icon
    look soft next to applications that install themselves properly."""
    src = os.path.join(SVG, 'icon_atomize.svg')
    base = os.path.join(ROOT, DESKTOP_DIR)
    apps = os.path.join(base, 'hicolor', 'scalable', 'apps')

    with open(src, 'rb') as fh:
        svg_data = fh.read()
    print('%-9s %s' % (write(os.path.join(apps, DESKTOP_ICON_NAME + '.svg'),
                             svg_data, check),
                       DESKTOP_DIR + '/hicolor/scalable/apps/%s.svg' % DESKTOP_ICON_NAME))

    for s in DESKTOP_SIZES:
        rel = 'hicolor/%dx%d/apps/%s.png' % (s, s, DESKTOP_ICON_NAME)
        data = png_bytes(render(src, s, s))
        print('%-9s %s' % (write(os.path.join(base, rel), data, check),
                           DESKTOP_DIR + '/' + rel))

    entry = DESKTOP_ENTRY.replace('__EXEC__', 'atomize-itc').encode('utf-8')
    print('%-9s %s' % (write(os.path.join(base, DESKTOP_ICON_NAME + '.desktop'),
                             entry, check),
                       DESKTOP_DIR + '/%s.desktop' % DESKTOP_ICON_NAME))

    for name in sorted(tool_icons()):
        tool = name[len('icon_'):]
        theme = '%s-%s' % (DESKTOP_ICON_NAME, tool)
        tsrc = os.path.join(SVG, name + '.svg')
        with open(tsrc, 'rb') as fh:
            write(os.path.join(apps, theme + '.svg'), fh.read(), check)
        for s in DESKTOP_SIZES:
            write(os.path.join(base, 'hicolor/%dx%d/apps/%s.png' % (s, s, theme)),
                  png_bytes(render(tsrc, s, s)), check)
        entry = (TOOL_ENTRY.replace('__NAME__', 'Atomize ' + tool)
                           .replace('__ICON__', theme)
                           .replace('__WMCLASS__', theme).encode('utf-8'))
        print('%-9s %s  (+ %d sizes)'
              % (write(os.path.join(base, theme + '.desktop'), entry, check),
                 DESKTOP_DIR + '/%s.desktop' % theme, len(DESKTOP_SIZES) + 1))


def main():
    check = '--check' in sys.argv[1:]
    QApplication(sys.argv)
    for key, rel in sorted(ico_targets().items()):
        src = os.path.join(SVG, key + '.svg')
        print('%-9s %s' % (write(os.path.join(ROOT, rel), ico_bytes(src), check), rel))
    for key, rel, w, h in PNG_TARGETS:
        src = os.path.join(SVG, key + '.svg')
        data = png_bytes(render(src, w, h))
        print('%-9s %s  %dx%d' % (write(os.path.join(ROOT, rel), data, check),
                                  rel, w, h))
    stage_desktop(check)


if __name__ == '__main__':
    main()
