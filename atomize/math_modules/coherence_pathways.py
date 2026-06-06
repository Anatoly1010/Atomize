#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coherence transfer pathways and phase cycling (math core).

Two related pure-Python utilities for designing and checking pulse-EPR phase
cycles. No hardware, no GUI, no NumPy/scipy -- just integer bookkeeping.

1. ``expand_phase_cycling`` turns a compact phase-cycle notation into the
   explicit per-step phase of every pulse and the matching receiver phase.
   Notation: ``+x/+y/-x/-y`` (or ``x/y/-x/-y``), comma lists for an explicit
   cycle, ``(...)`` for a 2-step (180 deg) nested cycle, ``[...]`` for a 4-step
   (90 deg quadrature) nested cycle, and a numeric-coefficient receiver such as
   ``'-1,2'`` (the per-pulse coherence-order weights) that is turned into the
   receiver phase automatically.

2. ``analyze_pathways`` enumerates every coherence transfer pathway and decides
   which the phase cycle keeps and which it phases out, locates each surviving
   echo on the time axis, and flags free-induction decays (FIDs). A pathway is
   the list of electron coherence orders ``p in {-1, 0, +1}`` during each delay,
   starting from equilibrium (``p = 0``) and ending at the detected order
   ``-1``, so an n-pulse sequence has ``3**(n-1)`` pathways. A pathway survives
   iff its acquired phase ``-sum(dp_i * phi_i)`` tracks the receiver across every
   step of the cycle (otherwise the steps co-add to zero); the desired pathway
   survives by construction, anything else that survives is an artefact the cycle
   fails to remove. An echo forms where ``sum_k p_k * tau_k`` over the sequence
   vanishes, i.e. at ``t_last_pulse + sum_k p_k * tau_k``; an FID is the special
   pathway that becomes observable at one pulse and is never refocused, so its
   echo sits exactly on that pulse.

Method follows Stoll & Kasumaj, Appl. Magn. Reson. 35, 15 (2008), and the DEER
artefact analysis of Spindler/Prisner et al., Phys. Chem. Chem. Phys. 18, 17223
(2016). The phase arithmetic here is the same one the EPR-endstation acquisition
tools apply at runtime, so the expansion is byte-for-byte what the hardware does.

Caveat: this is a *selection-rule / bookkeeping* tool. It lists which pathways
the phase cycle lets through, NOT their amplitudes. Phase-cycle selection depends
only on the coherence-order change ``dp``, so it is exact for real (non-ideal)
pulses; but whether a surviving pathway is actually excited, and how strongly,
depends on pulse flip angle / bandwidth / resonator / offset and is not modelled
here. Relaxation and nuclear coherences (ESEEM/HYSCORE modulation amplitudes) are
out of scope; electron coherence orders are restricted to -1/0/+1 (S = 1/2).

Conventions: positions and echo times are in whatever unit you pass in (ns is
typical); ``recv`` and per-pulse phases use the notation above. Times and orders
are plain Python numbers, so results drop straight into ``general.message(...)``.

    import atomize.math_modules.coherence_pathways as coh
"""

import re
import math
import itertools


# --------------------------------------------------------------------------- #
# Phase-cycle expansion
# --------------------------------------------------------------------------- #
def expand_phase_cycling(p_input, *pulse_args):
    """Expand short phase notation into explicit per-step phase lists.

    Understands ``+x/+y/-x/-y``, comma lists, ``[...]`` (4-step quadrature),
    ``(...)`` (2-step), and a numeric-coefficient receiver (e.g. ``-1,2``).

    Parameters
    ----------
    p_input : str or list
        Receiver specification: either explicit phase notation (``'+x,-x'``) or
        the per-pulse coherence-order coefficients (``'-1,2'`` / ``[-1, 2]``)
        from which the receiver phase is computed.
    *pulse_args : str
        One phase specification per pulse, in pulse order.

    Returns
    -------
    dict
        ``{"pulses": [[phase per step] per pulse], "receiver": [phase per step]}``
        with phases as ``'+x'/'+y'/'-x'/'-y'`` strings.
    """
    phases = ['+x', '+y', '-x', '-y']
    norm = {'x': 0, 'y': 1, '-x': 2, '-y': 3, '+': 0, '-': 2, 'i': 1, '-i': 3, '0': 0}

    def parse_to_indices(s):
        if not s:
            return [0]
        if isinstance(s, list):
            return [phases.index(p.strip()) if p.strip() in phases else norm.get(p.strip().lower().replace(' ', ''), 0) for p in s]

        s_clean = s.replace(' ', '')
        if ',' in s_clean:
            parts = [p for p in s_clean.split(',') if p]
            return [phases.index(p) if p in phases else norm.get(p.lower(), 0) for p in parts]

        def get_recursive(st):
            st = st.replace('D', '').lower().replace(' ', '')
            if not st:
                return [0]
            if '[' not in st and '(' not in st:
                return [norm.get(st.strip(), 0)]
            is_quad = st.startswith('[')
            inner = get_recursive(st[1:-1])
            steps, shift = (4, 1) if is_quad else (2, 2)
            return [(p_idx + step * shift) % 4 for step in range(steps) for p_idx in inner]

        return get_recursive(s_clean)

    raw_sequences = [parse_to_indices(arg) for arg in pulse_args]

    target_len = 1
    for i, seq in enumerate(raw_sequences):
        arg = pulse_args[i]
        if isinstance(arg, str) and ('(' in arg or '[' in arg):
            if len(seq) > 1:
                target_len *= len(seq)

    if target_len == 1:
        for seq in raw_sequences:
            if len(seq) > 1:
                target_len = abs(target_len * len(seq)) // math.gcd(target_len, len(seq))

    if target_len < 2:
        target_len = 2

    pulses_final = []
    current_repeat = 1
    for i, seq in enumerate(raw_sequences):
        arg = pulse_args[i]
        if isinstance(arg, str) and ('(' in arg or '[' in arg):
            expanded = [p for p in seq for _ in range(current_repeat)]
            final = (expanded * (target_len // len(expanded) + 1))[:target_len]
            current_repeat *= len(seq)
        else:
            final = (seq * (target_len // len(seq) + 1))[:target_len]
        pulses_final.append(final)

    if isinstance(p_input, (list, str)) and not any(ph in str(p_input).lower() for ph in ['x', 'y']):
        if isinstance(p_input, str):
            coeffs = [float(x) for x in re.findall(r'-?\d+\.?\d*', p_input)]
        else:
            coeffs = p_input

        receiver_indices = []
        for step in range(target_len):
            rec_sum = sum(coeffs[i] * pulses_final[i][step]
                          for i in range(min(len(coeffs), len(pulses_final))))
            receiver_indices.append(int(round(rec_sum)) % 4)
    else:
        det_indices = parse_to_indices(p_input)
        receiver_indices = (det_indices * (target_len // len(det_indices) + 1))[:target_len]

    to_str = lambda indices: [phases[i] for i in indices]
    return {"pulses": [to_str(p) for p in pulses_final], "receiver": to_str(receiver_indices)}


# --------------------------------------------------------------------------- #
# Coherence transfer pathway analysis
# --------------------------------------------------------------------------- #
# Electron-spin coherence orders during a delay (S = 1/2: no multiple quantum).
COH_ORDERS = (-1, 0, 1)
COH_SYM = {-1: '-', 0: '0', 1: '+'}


def positions_from_taus(taus, base=0.0, grid=None):
    """Cumulative absolute pulse positions from inter-pulse delays.

    The first pulse sits at ``base`` and each subsequent one is ``+tau`` later.
    With ``grid`` set, every position is snapped up to that grid (ceil), matching
    the hardware timing raster; leave it ``None`` for exact positions.

    Returns the list of pulse positions (length ``len(taus) + 1``).
    """
    def snap(v):
        if not grid:
            return v
        q = v / grid
        return round(grid * (int(q) + (round(v % grid, 6) > 0)), 6)
    pos = [float(base)]
    for t in taus:
        pos.append(snap(pos[-1] + t))
    return pos


def analyze_pathways(recv, pulse_phase_strs, positions, det_pos):
    """Enumerate coherence transfer pathways and classify them by phase cycle.

    Parameters
    ----------
    recv : str or list
        Receiver specification (see :func:`expand_phase_cycling`) -- typically
        the per-pulse coherence-order coefficients, e.g. ``'-1,2'`` for a Hahn
        echo or ``'1,-2,0,2'`` for 4-pulse DEER.
    pulse_phase_strs : list of str
        Phase-cycle notation for each pulse, in order (e.g. ``['(x)', 'x']``).
    positions : list of float
        Absolute start position of each pulse, same length as
        ``pulse_phase_strs``. See :func:`positions_from_taus`.
    det_pos : float
        Absolute position of the detection window (echo centre of the desired
        pathway).

    Returns
    -------
    dict
        ``{total, steps, det_pos, suppressed, survivors, fids}`` where

        * ``total`` -- number of pathways enumerated, ``3**(n-1)``;
        * ``steps`` -- number of phase-cycle steps;
        * ``suppressed`` -- count of pathways the cycle removes;
        * ``survivors`` -- list of dicts ``{p, dp, echo, desired, fid, role}``;
          ``p`` is the per-delay orders ``p[1..n]`` (detection last), ``dp`` the
          per-pulse changes, ``echo`` the absolute echo position, ``desired``
          True if the echo lands on the detection window, ``fid`` the pulse
          number if the pathway is that pulse's FID (else ``None``), ``role`` a
          human-readable label;
        * ``fids`` -- per-pulse FID bookkeeping, list of
          ``{pulse, echo, survives}`` for every pulse whether kept or removed.
    """
    phase_list = ['+x', '+y', '-x', '-y']
    pidx = {s: i for i, s in enumerate(phase_list)}
    n = len(pulse_phase_strs)
    res = expand_phase_cycling(recv, *pulse_phase_strs)
    steps = len(res["receiver"])
    pulse_ix = [[pidx[res["pulses"][i][s]] for s in range(steps)] for i in range(n)]
    rec_ix = [pidx[res["receiver"][s]] for s in range(steps)]

    def survives(p):
        dp = [p[i + 1] - p[i] for i in range(n)]
        offs = {(-sum(dp[i] * pulse_ix[i][s] for i in range(n)) - rec_ix[s]) % 4
                for s in range(steps)}
        return len(offs) == 1

    def echo_of(p):
        return positions[-1] + sum(p[k] * (positions[k] - positions[k - 1])
                                   for k in range(1, n))

    def fid_pulse(echo):                     # echo sitting on a pulse -> that FID
        for k in range(n):
            if abs(echo - positions[k]) <= 1.6:
                return k + 1
        return None

    survivors = []
    suppressed = 0
    for mids in itertools.product(COH_ORDERS, repeat=max(0, n - 1)):
        p = [0] + list(mids) + [-1]          # p[0]=equilibrium ... p[n]=detection
        if not survives(p):
            suppressed += 1
            continue
        echo = echo_of(p)
        desired = abs(echo - det_pos) <= 1.6
        fid = fid_pulse(echo)
        if desired:
            role = "DETECTED (echo on window)"
        elif fid is not None:
            role = "FID from P%d" % fid
        else:
            role = "artefact echo (%+.1f off window)" % (echo - det_pos)
        survivors.append({"p": p[1:], "dp": [p[i + 1] - p[i] for i in range(n)],
                          "echo": echo, "desired": desired, "fid": fid, "role": role})
    survivors.sort(key=lambda s: (not s["desired"], s["echo"]))

    # FID bookkeeping for every pulse, kept or removed by the cycle
    fids = []
    for j in range(1, n + 1):
        p = [0] + [0] * (j - 1) + [-1] * (n - j) + [-1]
        fids.append({"pulse": j, "echo": positions[j - 1], "survives": survives(p)})

    return {"total": 3 ** max(0, n - 1), "steps": steps, "det_pos": det_pos,
            "survivors": survivors, "suppressed": suppressed, "fids": fids}


def pathway_report(recv, pulse_phase_strs, positions, det_pos):
    """Human-readable multi-line summary of :func:`analyze_pathways`.

    Returns a string ready for ``print`` or ``general.message(...)``: the
    surviving pathways with their echo positions and roles, a per-pulse FID
    table, and the selection-rule caveat.
    """
    an = analyze_pathways(recv, pulse_phase_strs, positions, det_pos)
    out = []
    out.append("Coherence transfer pathways  (electron p in -1,0,+1; detection -1)")
    out.append("  %d pathways, %d-step cycle  ->  %d survive, %d phased out"
               % (an["total"], an["steps"], len(an["survivors"]), an["suppressed"]))
    out.append("  pathway (per delay, detection last) | echo | role")
    out.append("  " + "-" * 52)
    for s in an["survivors"]:
        notation = "".join(COH_SYM[x] for x in s["p"])
        out.append("  %-12s | %9.1f | %s" % (notation, s["echo"], s["role"]))
    out.append("")
    out.append("  FIDs (decay from each pulse; ideally only the echo is kept):")
    for f in an["fids"]:
        out.append("    P%d FID @ %9.1f  ->  %s"
                   % (f["pulse"], f["echo"], "kept" if f["survives"] else "phased out"))
    out.append("")
    out.append("  Note: lists pathways the phase cycle lets through, not their")
    out.append("  amplitudes. Excitation strength (flip angle / bandwidth / offset)")
    out.append("  and relaxation are NOT modelled; electron coherence only (S = 1/2).")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Self-test:  python -m atomize.math_modules.coherence_pathways
# --------------------------------------------------------------------------- #
def _self_test():
    # Phase-cycle expansion + auto receiver for a Hahn echo ([-1,2], (x), x).
    res = expand_phase_cycling('-1,2', '(x)', 'x')
    assert res["pulses"] == [['+x', '-x'], ['+x', '+x']], res["pulses"]
    assert res["receiver"] == ['+x', '-x'], res["receiver"]

    # Hahn: 3 pathways, 2 survive the 2-step cycle; only 0->+1->-1 refocuses on
    # the window, and the pi-pulse (P2) FID is the one pathway phased out.
    h = analyze_pathways('-1,2', ['(x)', 'x'], [0.0, 288.0], 576.0)
    assert h["total"] == 3 and len(h["survivors"]) == 2, h
    des = [s for s in h["survivors"] if s["desired"]]
    assert len(des) == 1 and des[0]["p"] == [1, -1] and des[0]["echo"] == 576.0, des
    assert [f["survives"] for f in h["fids"]] == [True, False], h["fids"]

    # 4p-DEER: 27 pathways, 6 survive the 8-step cycle, desired "-++-" on window.
    d = analyze_pathways('1,-2,0,2', ['(x)', 'x', '[x]', 'x'],
                         [0.0, 208.0, 320.0, 1936.0], 3456.0)
    assert d["total"] == 27 and len(d["survivors"]) == 6, d
    des = [s for s in d["survivors"] if s["desired"]]
    assert len(des) == 1 and des[0]["p"] == [-1, 1, 1, -1], des

    # positions_from_taus: cumulative, with optional grid snap (ceil).
    assert positions_from_taus([288, 288]) == [0.0, 288.0, 576.0]
    assert positions_from_taus([200], grid=3.2) == [0.0, 201.6]

    print("coherence_pathways self-test passed")


if __name__ == '__main__':
    _self_test()
    print()
    print(pathway_report('1,-2,0,2', ['(x)', 'x', '[x]', 'x'],
                         [0.0, 208.0, 320.0, 1936.0], 3456.0))
