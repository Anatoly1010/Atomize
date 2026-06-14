#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation suite for :mod:`atomize.math_modules.preset_loader`.

Parses the real shipped presets in ``control_center/experiments`` and checks
the loader builds physically-correct spin-dynamics sequences:

1. **Hahn echo** (AWG + RECT) -- two active pulses, the second pi at twice the
   length/coef of the first; the simulated echo lands at the analytic
   ``2*tau`` and tracks the detection window as the sweep steps; the AWG and
   RECT presets (same geometry, different idiom) give the same echo position.
2. **3-pulse ESEEM** -- three pi/2 pulses + a 4-step cycle; the modulation vs
   the stimulated-echo delay T matches the exact Mims formula, and the loader's
   parsed cycle has the right step count.
3. **4-pulse DEER** -- the loader puts the pump pulse at the right carrier
   offset (``freq - freq_obs``), parses the 8-step cycle, and the observer/pump
   split is read correctly.
+  parsing sanity (field counts, active-pulse selection, axis).
"""

import os
import sys
import time

import numpy as np

import atomize.math_modules.preset_loader as pl
import atomize.math_modules.spin_dynamics as sd

PI = np.pi
EXP = os.path.join(os.path.dirname(__file__), '..', '..',
                   'control_center', 'experiments')


def _p(name):
    return os.path.join(EXP, name)


# --------------------------------------------------------------------------- #
# Parsing sanity
# --------------------------------------------------------------------------- #
def test_parse_hahn_awg():
    pre = pl.parse_preset(_p('hahn_echo_4s.phase_awg'))
    assert pre.kind == 'awg'
    assert len(pre.pulses) == 2, "hahn AWG: expected 2 active pulses, got %d" % len(pre.pulses)
    p2, p3 = pre.pulses
    assert p2['shape'] == 'rectangular' and abs(p2['length'] - 22.4) < 1e-9
    assert p3['shape'] == 'rectangular' and abs(p3['length'] - 44.8) < 1e-9
    assert abs(p2['coef'] - 100) < 1e-9 and abs(p3['coef'] - 100) < 1e-9
    assert pre.detection['recv'] == '[-1,2]'
    assert abs(pre.globals['freq_obs'] - 50.0) < 1e-9


def test_parse_rect_hahn():
    pre = pl.parse_preset(_p('hahn_echo_4s.phase'))
    assert pre.kind == 'rect'
    assert len(pre.pulses) == 2
    assert pre.pulses[0]['shape'] == 'rectangular'
    assert abs(pre.pulses[1]['length'] - 44.8) < 1e-9     # pi by length
    assert pre.globals['freq_obs'] == 0.0                 # no freq field


def test_skip_inactive_and_laser():
    pre = pl.parse_preset(_p('4pdeer_8s.phase_awg'))
    # P2,P3,P4,P5 active (lengths 48/48/22.4/48), P6..P9 zero-length dropped.
    assert len(pre.pulses) == 4, "DEER: expected 4 active, got %d" % len(pre.pulses)


# --------------------------------------------------------------------------- #
# Rung 1: Hahn echo, AWG and RECT, position + window tracking
# --------------------------------------------------------------------------- #
SIGMA = 0.05


def _line(n=401, span=0.25):
    offs = np.linspace(-span, span, n)
    return offs, sd.gaussian_weights(offs, SIGMA)


# Pin the nutation so the Hahn presets are genuine pi/2 + pi (coef 100 at
# 22.4 ns = pi/2 in these presets); RECT ignores the coef part of flip_cal.
HAHN_CAL = (100.0, 22.4, 0.5 * PI)


def _echo_peak_time(pre, eng, step=0, flip_cal=HAHN_CAL):
    events, cyc = pre.build(step=step, detect_dt=0.5, flip_cal=flip_cal)
    win = eng.run(events, phase_cycle=cyc)[0]
    k = int(np.argmax(np.abs(win['v'])))
    return win['t'][k], np.abs(win['v'][k]), win


def test_hahn_awg_echo_position():
    pre = pl.parse_preset(_p('hahn_echo_4s.phase_awg'))
    offs, w = _line()
    eng = sd.Engine(sd.SpinSystem((0.5,)), offsets=offs, weights=w)
    # The flip calibration here is the default; for the echo *position* only the
    # timing matters. pi/2 at coef 100/len 22.4 is a big flip, but the refocused
    # transverse magnetisation still peaks at 2*tau regardless of exact angle.
    tpk, amp, win = _echo_peak_time(pre, eng)
    p2, p3 = sorted(pre.pulses, key=lambda q: q['start'])
    # tau measured pulse-centre to pulse-centre; echo at t = 2*tau from pulse 1
    # centre. Build() sets t=0 at the first pulse's *leading edge*.
    c1 = (p2['start'] - p2['start']) + 0.5 * p2['length']        # = 11.2
    c2 = (p3['start'] - p2['start']) + 0.5 * p3['length']
    tau = c2 - c1
    expect = c1 + 2.0 * tau
    # 2*tau is the ideal centre-to-centre echo time; finite pulses on a line
    # broader than their bandwidth shift the envelope peak by a few ns (the
    # AWG/RECT cross-check below pins that the loader itself is consistent).
    assert abs(tpk - expect) < 4.0, "AWG Hahn echo at %.1f, expected ~%.1f" % (tpk, expect)
    assert amp > 0.05, "AWG Hahn echo vanished (amp %.3g)" % amp
    # Echo must fall inside the detection window the preset defines.
    assert win['t'][0] <= tpk <= win['t'][-1]


def test_hahn_rect_matches_awg_position():
    pre_a = pl.parse_preset(_p('hahn_echo_4s.phase_awg'))
    pre_r = pl.parse_preset(_p('hahn_echo_4s.phase'))
    offs, w = _line()
    ea = sd.Engine(sd.SpinSystem((0.5,)), offsets=offs, weights=w)
    er = sd.Engine(sd.SpinSystem((0.5,)), offsets=offs, weights=w)
    ta, _, _ = _echo_peak_time(pre_a, ea)
    tr, _, _ = _echo_peak_time(pre_r, er)
    assert abs(ta - tr) < 1.0, "AWG vs RECT echo position: %.1f vs %.1f" % (ta, tr)


def test_hahn_window_tracks_with_step():
    pre = pl.parse_preset(_p('hahn_echo_4s.phase_awg'))
    offs, w = _line()
    eng = sd.Engine(sd.SpinSystem((0.5,)), offsets=offs, weights=w)
    # P3 (pi) has st_inc 6.4; stepping moves tau by 6.4 -> echo by 2*6.4 = 12.8,
    # and detection st_inc is 12.8, so the echo stays centred in the window.
    t0, _, w0 = _echo_peak_time(pre, eng, step=0)
    t5, _, w5 = _echo_peak_time(pre, eng, step=5)
    assert abs((t5 - t0) - 5 * 12.8) < 1.0, "echo did not move 2*dtau: %.1f" % (t5 - t0)
    # window centre offset of the echo stays ~constant (tracking works)
    off0 = t0 - 0.5 * (w0['t'][0] + w0['t'][-1])
    off5 = t5 - 0.5 * (w5['t'][0] + w5['t'][-1])
    assert abs(off0 - off5) < 1.0, "echo drifted in the window: %.1f -> %.1f" % (off0, off5)


# --------------------------------------------------------------------------- #
# Rung 2: 3-pulse ESEEM preset vs Mims, and cycle step count
# --------------------------------------------------------------------------- #
NU_I, A_HF, B_HF = 0.0149, 0.0040, 0.0030


def _eseem_sys(b):
    s = sd.SpinSystem((0.5, 0.5))
    s.zeeman(1, NU_I)
    s.hyperfine(0, 1, A=A_HF, B=b)
    return s


def _mims_3p(tau, T):
    na = np.hypot(NU_I + 0.5 * A_HF, 0.5 * B_HF)
    nb = np.hypot(NU_I - 0.5 * A_HF, 0.5 * B_HF)
    k = (B_HF * NU_I / (na * nb)) ** 2
    wa, wb = 2 * PI * na, 2 * PI * nb
    return 1.0 - 0.25 * k * (
        (1 - np.cos(wa * tau)) * (1 - np.cos(wb * (tau + T)))
        + (1 - np.cos(wb * tau)) * (1 - np.cos(wa * (tau + T))))


def test_3peseem_preset_cycle_count():
    pre = pl.parse_preset(_p('3peseem_4s.phase_awg'))
    assert len(pre.pulses) == 3, "3p-ESEEM: expected 3 pulses, got %d" % len(pre.pulses)
    _, cyc = pre.build(step=0)
    assert cyc is not None and len(cyc) == 4, "expected 4-step cycle, got %r" % (
        None if cyc is None else len(cyc))


def test_3peseem_preset_vs_mims():
    pre = pl.parse_preset(_p('3peseem_4s.phase_awg'))
    # The preset's 4-step cycle is the *broad-line* stimulated-echo cycle: the
    # unwanted (mirror / FID) pathways form away from the stimulated echo and
    # dephase across an inhomogeneous line, which is what lets the 4-step cycle
    # select cleanly (a single packet leaks ~5%, see the engine's own 8-step
    # suite). So evaluate over a Gaussian line -- the Mims ratio is itself
    # offset-independent, so the modulation is preserved. Timing and the phase
    # cycle both come from the loader; the hardware coef is swapped for ideal
    # pi/2 rotations so the comparison is against the closed form.
    offs = np.linspace(-0.2, 0.2, 401)
    w = sd.gaussian_weights(offs, 0.06)
    eng = sd.Engine(_eseem_sys(B_HF), offsets=offs, weights=w)
    ref = sd.Engine(_eseem_sys(0.0), offsets=offs, weights=w)

    p = sorted(pre.pulses, key=lambda q: q['start'])
    tau = (p[1]['start'] + 0.5 * p[1]['length']) - (p[0]['start'] + 0.5 * p[0]['length'])
    _, cyc = pre.build(step=0)                  # the loaded 4-step cycle
    flip = sd.Pulse(flip=0.5 * PI)

    Ts = np.arange(40.0, 600.0, 12.0)
    V = np.empty(Ts.size)
    for i, T in enumerate(Ts):
        seq = [flip, sd.Delay(tau), flip, sd.Delay(T), flip, sd.Delay(tau),
               sd.Detect()]
        v = eng.run(seq, phase_cycle=cyc)[0]['v'][0]
        v0 = ref.run(seq, phase_cycle=cyc)[0]['v'][0]
        V[i] = (v / v0).real
    err = np.max(np.abs(V - _mims_3p(tau, Ts)))
    assert err < 1e-2, "3p-ESEEM preset vs Mims (broad line): %.3e" % err


# --------------------------------------------------------------------------- #
# Rung 3: DEER pump carrier offset + cycle
# --------------------------------------------------------------------------- #
def test_deer_pump_offset_and_cycle():
    pre = pl.parse_preset(_p('4pdeer_8s.phase_awg'))
    obs = pre.globals['freq_obs']
    assert abs(obs - 25.0) < 1e-9, "DEER observer freq %r" % obs
    events, cyc = pre.build(step=0)
    # one pulse must carry a non-zero centre = pump offset (100 - 25 = 75 MHz)
    centers = [ev.params.get('center', 0.0) for ev in events if isinstance(ev, sd.Pulse)]
    assert any(abs(c - 75.0) < 1e-9 for c in centers), \
        "no pump pulse at +75 MHz; centres = %r" % centers
    # observer pulses sit at centre 0
    assert sum(abs(c) < 1e-9 for c in centers) == 3, "expected 3 on-observer pulses"
    assert cyc is not None and len(cyc) == 8, "expected 8-step DEER cycle, got %r" % (
        None if cyc is None else len(cyc))


def test_sweep_axis():
    pre = pl.parse_preset(_p('3peseem_4s.phase_awg'))
    ax = pre.sweep_axis()
    assert ax.size == 500, "sweep points %d" % ax.size       # 2nd 'Points' line
    # dX == 0 in this preset -> auto from first non-zero st_inc (P4 = 12.8)
    assert abs((ax[1] - ax[0]) - 12.8) < 1e-9, "auto axis step %.3f" % (ax[1] - ax[0])


# --------------------------------------------------------------------------- #
TESTS = [
    test_parse_hahn_awg,
    test_parse_rect_hahn,
    test_skip_inactive_and_laser,
    test_hahn_awg_echo_position,
    test_hahn_rect_matches_awg_position,
    test_hahn_window_tracks_with_step,
    test_3peseem_preset_cycle_count,
    test_3peseem_preset_vs_mims,
    test_deer_pump_offset_and_cycle,
    test_sweep_axis,
]


def main():
    failed = 0
    for fn in TESTS:
        t0 = time.time()
        try:
            fn()
            print("PASS  %-40s (%.2f s)" % (fn.__name__, time.time() - t0))
        except Exception as exc:
            failed += 1
            print("FAIL  %-40s %s" % (fn.__name__, exc))
    print("-" * 62)
    print("%d/%d passed" % (len(TESTS) - failed, len(TESTS)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
