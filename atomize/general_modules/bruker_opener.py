#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reader for Bruker native EPR data formats (numpy-only, no extra dependencies).

Two families are supported:

  * BES3T  — Xepr / Elexsys (.DSC descriptor + .DTA binary, plus optional
    .XGF/.YGF companion files for non-linear axes). The modern pulse-EPR
    format; complex datasets (IKKF=CPLX) carry quadrature data and map onto an
    I/Q pair. Binary is big-endian by default (BSEQ), data type from IRFMT.
  * ESP / WinEPR — older EMX (.par ASCII + .spc binary). WinEPR (PC) is
    little-endian float32; ESP (workstation) is big-endian int32. Mostly CW.

`Bruker_Opener().open(path)` accepts any member of the pair (descriptor or
binary) and returns a dict:

    {'format', 'ndim', 'x', 'x_name', 'x_unit', 'y', 'y_name', 'y_unit',
     'channels': [(label, ndarray), ...], 'complex', 'data', 'params'}

`channels` is what the 1D Data Treatment tool registers: [('real', ...),
('imag', ...)] for complex data, else [('intensity', ...)]. `data` is the raw
shaped array (complex when applicable): (nx,) for 1D, (ny, nx) for 2D.

The reader is hardware-agnostic and headless (no Qt), so it is reusable for
any Bruker trace — T1/T2 relaxation, CW spectra, ESEEM, DEER, etc.
"""

import os
import numpy as np

# BES3T IRFMT/IIFMT data-type codes -> numpy base type
_BES3T_FMT = {'D': 'f8', 'F': 'f4', 'I': 'i4', 'S': 'i2', 'C': 'i1', 'B': 'i1'}


class Bruker_Opener:

    # ------------------------------------------------------------------ public
    def open(self, path):
        """Open a Bruker file (BES3T or ESP/WinEPR); dispatch on the extension."""
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.dsc', '.dta', '.xgf', '.ygf', '.zgf'):
            return self.read_bes3t(path)
        if ext in ('.par', '.spc'):
            return self.read_winepr(path)
        raise ValueError(f'Not a recognized Bruker file: {path}')

    # ------------------------------------------------------------------ BES3T
    def read_bes3t(self, path):
        dsc, dta = self._pair(path, '.dsc', '.dta')
        P = self._parse_dsc(self._read_text(dsc))

        endian = '<' if P.get('BSEQ', 'BIG').upper().startswith('LIT') else '>'
        rfmt = _BES3T_FMT.get(P.get('IRFMT', 'D').upper(), 'f8')
        is_cplx = 'CPLX' in P.get('IKKF', 'REAL').upper()

        xpts = int(float(P['XPTS']))
        ypts = int(float(P.get('YPTS', 1)))
        ndim = 2 if ypts > 1 else 1

        flat = np.fromfile(dta, dtype=np.dtype(endian + rfmt)).astype(np.float64)
        n = xpts*ypts
        if is_cplx:
            flat = flat[:2*n]
            data = flat[0::2] + 1j*flat[1::2]
        else:
            data = flat[:n]
        data = data.reshape(ypts, xpts) if ndim == 2 else data.reshape(xpts)

        x = self._bes3t_axis(P, 'X', xpts, endian,
                             self._companion(dta, '.xgf'))
        x_name = self._unquote(P.get('XNAM', '')) or 'X'
        x_unit = self._unquote(P.get('XUNI', ''))
        y = y_name = y_unit = None
        if ndim == 2:
            y = self._bes3t_axis(P, 'Y', ypts, endian,
                                self._companion(dta, '.ygf'))
            y_name = self._unquote(P.get('YNAM', '')) or 'Y'
            y_unit = self._unquote(P.get('YUNI', ''))

        ord_name = self._unquote(P.get('IRNAM', '')) or 'intensity'
        channels = self._channels(data, is_cplx, ord_name, ndim)
        return {'format': 'BES3T', 'ndim': ndim, 'x': x, 'x_name': x_name,
                'x_unit': x_unit, 'y': y, 'y_name': y_name, 'y_unit': y_unit,
                'channels': channels, 'complex': is_cplx, 'data': data,
                'params': P}

    def _bes3t_axis(self, P, ax, npts, endian, companion):
        """Build the BES3T abscissa for axis 'X' or 'Y' (linear IDX, or read the
        companion .XGF/.YGF file for the non-linear IGD case)."""
        if P.get(f'{ax}TYP', 'IDX').upper() == 'IGD' and companion:
            a = np.fromfile(companion, dtype=np.dtype(endian + 'f8'))
            if a.size >= npts:
                return a[:npts].astype(np.float64)
        mn = float(P.get(f'{ax}MIN', 0.0))
        wid = float(P.get(f'{ax}WID', max(npts - 1, 1)))
        if npts < 2:
            return np.array([mn], dtype=float)
        return mn + np.arange(npts)*wid/(npts - 1)

    # ------------------------------------------------------------ ESP / WinEPR
    def read_winepr(self, path):
        par, spc = self._pair(path, '.par', '.spc')
        P = self._parse_par(self._read_text(par))

        winepr = 'DOS' in P                       # WinEPR writes a 'DOS Format' line
        dtype = np.dtype('<f4') if winepr else np.dtype('>i4')

        nx = int(float(P.get('SSX') or P.get('ANZ') or P.get('RES') or 0))
        ny = int(float(P.get('SSY', 1)))
        ndim = 2 if ny > 1 else 1

        flat = np.fromfile(spc, dtype=dtype).astype(np.float64)
        if nx <= 0:
            nx = flat.size // max(ny, 1)
        data = (flat[:nx*ny].reshape(ny, nx) if ndim == 2 else flat[:nx])

        x, x_name, x_unit = self._winepr_axis(P, nx)
        channels = self._channels(data, False, 'intensity', ndim)
        return {'format': 'WinEPR' if winepr else 'ESP', 'ndim': ndim, 'x': x,
                'x_name': x_name, 'x_unit': x_unit, 'y': None, 'y_name': None,
                'y_unit': None, 'channels': channels, 'complex': False,
                'data': data, 'params': P}

    def _winepr_axis(self, P, nx):
        """Abscissa from a generic GST/GSI sweep, else an HCF/HSW field sweep."""
        if nx < 2:
            return np.arange(max(nx, 1), dtype=float), 'X', ''
        if 'GST' in P and 'GSI' in P:
            gst, gsi = float(P['GST']), float(P['GSI'])
            return gst + np.arange(nx)*gsi/(nx - 1), 'X', self._unquote(P.get('JUN', ''))
        if 'HCF' in P and 'HSW' in P:
            hcf, hsw = float(P['HCF']), float(P['HSW'])
            return hcf + (np.arange(nx)/(nx - 1) - 0.5)*hsw, 'Field', 'G'
        return np.arange(nx, dtype=float), 'X', ''

    # ------------------------------------------------------------------ shared
    @staticmethod
    def _channels(data, is_cplx, ord_name, ndim):
        if ndim != 1:
            return [(ord_name, data)]            # 2D handled by the caller
        if is_cplx:
            return [('real', np.real(data)), ('imag', np.imag(data))]
        return [(ord_name, np.asarray(data, dtype=float))]

    @staticmethod
    def _parse_dsc(text):
        """Parse a BES3T .DSC into {KEY: value-string}. Lines are 'KEY value';
        '*', '#' and '.DVC' section markers are skipped; quotes are kept raw."""
        out = {}
        for line in text.splitlines():
            s = line.strip()
            if not s or s[0] in '*#;' or s.startswith('.DVC'):
                continue
            parts = s.split(None, 1)
            key = parts[0]
            if key not in out:                   # keep the first (header) value
                out[key] = parts[1].strip() if len(parts) > 1 else ''
        return out

    @staticmethod
    def _parse_par(text):
        """Parse an ESP/WinEPR .par into {KEY: value-string}."""
        out = {}
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            parts = s.split(None, 1)
            out[parts[0]] = parts[1].strip() if len(parts) > 1 else ''
        return out

    @staticmethod
    def _unquote(s):
        return s.strip().strip("'").strip('"').strip() if s else ''

    @staticmethod
    def _read_text(path):
        # Bruker descriptors are latin-1 / ascii; be tolerant of stray bytes.
        with open(path, 'r', encoding='latin-1') as fh:
            return fh.read()

    @staticmethod
    def _companion(data_path, ext):
        base = os.path.splitext(data_path)[0]
        for e in (ext, ext.upper()):
            cand = base + e
            if os.path.isfile(cand):
                return cand
        return None

    def _pair(self, path, desc_ext, data_ext):
        """Given any member of a Bruker pair, return (descriptor, data) paths
        with case-insensitive extension matching."""
        base = os.path.splitext(path)[0]
        desc = self._find(base, desc_ext)
        data = self._find(base, data_ext)
        if desc is None or data is None:
            missing = desc_ext if desc is None else data_ext
            raise FileNotFoundError(
                f'Missing the {missing} companion next to {os.path.basename(path)}')
        return desc, data

    @staticmethod
    def _find(base, ext):
        for e in (ext, ext.upper(), ext.lower()):
            cand = base + e
            if os.path.isfile(cand):
                return cand
        return None
