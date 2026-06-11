# Bruker native formats

A separate, dependency-free reader opens **Bruker EPR native files** directly,
without converting to CSV first. It is numpy-only (no Qt, no extra packages) and
hardware-agnostic, so it works for any Bruker trace — CW spectra, T1/T2
relaxation, ESEEM, DEER, etc.

```python
import atomize.general_modules.bruker_opener as bruker

reader = bruker.Bruker_Opener()
data = reader.open('my_measurement.DSC')
```

Two format families are supported:

- **BES3T** — Xepr / Elexsys (`.DSC` ASCII descriptor + `.DTA` binary, plus
  optional `.XGF`/`.YGF` companions for non-linear axes). The modern pulse-EPR
  format; complex datasets (`IKKF=CPLX`) carry quadrature data and map onto an
  I/Q pair.
- **ESP / WinEPR** — older EMX (`.par` ASCII + `.spc` binary). WinEPR (PC) is
  little-endian float32; ESP (workstation) is big-endian int32. Mostly CW.

## Functions { #bruker_functions data-toc-label="Functions" }

### Bruker_Opener() { #Bruker_Opener data-toc-label="Bruker_Opener" }

```python
reader = bruker.Bruker_Opener()
```

Creates the reader. All methods below are called on it.

### open(path) { #bruker_open data-toc-label="open" }

```python
data = reader.open(path)    # -> dict
```

Opens a Bruker file and dispatches on the extension: `.dsc`/`.dta`/`.xgf`/`.ygf`
→ [`read_bes3t()`](#read_bes3t); `.par`/`.spc` → [`read_winepr()`](#read_bes3t).
You may pass **either** member of a pair (the descriptor or the binary) — the
companion file is found automatically. Raises `ValueError` for an unrecognized
extension.

The returned dict:

| Key | Description |
| --- | ----------- |
| `format` | `'BES3T'` or `'ESP/WinEPR'` |
| `ndim` | `1` or `2` |
| `x` | The X (within-trace) abscissa array |
| `x_name`, `x_unit` | X axis name and unit (from the descriptor) |
| `y` | The Y (indirect) abscissa array (2D only) |
| `y_name`, `y_unit` | Y axis name and unit |
| `complex` | `True` if the data carry quadrature (I/Q) |
| `data` | Raw shaped array — `(nx,)` for 1D, `(ny, nx)` for 2D; complex when applicable |
| `channels` | `[(label, ndarray), …]`: `[('real', …), ('imag', …)]` for complex data, else `[('intensity', …)]` |
| `params` | The parsed descriptor as a `{key: value}` dict |

`channels` is the convenient form the Data Treatment tools register; `data` is
the raw array for direct numerical work.

### read_bes3t(path) / read_winepr(path) { #read_bes3t data-toc-label="read_bes3t / read_winepr" }

```python
data = reader.read_bes3t(path)     # BES3T (.DSC/.DTA)
data = reader.read_winepr(path)    # ESP/WinEPR (.par/.spc)
```

The per-format readers behind [`open()`](#bruker_open); both return the same
dict described above. Call them directly when you already know the format,
otherwise prefer [`open()`](#bruker_open).

```python
import atomize.general_modules.bruker_opener as bruker
import atomize.general_modules.general_functions as general

reader = bruker.Bruker_Opener()
res = reader.open('echo_decay.DSC')
if res['complex']:
    re = dict(res['channels'])['real']
    general.plot_1d('Bruker', res['x'], re, xname='Time', xscale=res['x_unit'])
```
