#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation suite for :mod:`atomize.math_modules.spin_dynamics`.

Run directly (``python test_spin_dynamics.py``) or via pytest. The ladder:

1. **Bloch limit** -- a bare S = 1/2 must reproduce the independent Bloch-
   vector module :mod:`pulse_excitation` to ~machine precision, for single
   shaped pulses (incl. resonator + ring-down) and a pulse-delay-pulse chain.
2. **Hahn echo** -- echo position, phase and shape against the analytic
   result for a Gaussian inhomogeneous line; flip-angle scaling
   ``E ~ sin(b1) sin^2(b2/2)``; phenomenological Tm and T1 against their
   exact exponentials.
3. **ESEEM** -- 2-pulse and 3-pulse echo modulation against the *exact* Mims
   formulas (S = 1/2, I = 1/2, ideal pulses). The 3-pulse test runs an
   8-step pathway-selective phase cycle, so it also validates the
   phase-cycling machinery (and asserts that *without* the cycle the
   single-packet signal is contaminated -- the cycle really does the work).
+  dt-convergence (2nd-order step error) and unitarity/purity checks.
"""

import sys
import time

import numpy as np

import atomize.math_modules.pulse_excitation as pex
import atomize.math_modules.spin_dynamics as sd

PI = np.pi


def _bloch(engine, system):
    """Mx, My, Mz per ensemble member from the engine's final rho (S = 1/2)."""
    mx = 2.0 * engine.expect(system.op(0, 'x')).real
    my = 2.0 * engine.expect(system.op(0, 'y')).real
    mz = 2.0 * engine.expect(system.op(0, 'z')).real
    return mx, my, mz


# --------------------------------------------------------------------------- #
# Rung 1: S = 1/2 limit == Bloch module
# --------------------------------------------------------------------------- #
def test_bloch_limit_single_pulses():
    offsets = np.linspace(-0.15, 0.15, 201)
    res = {'nu0': 9.5, 'Q': 100.0, 'mode': 'simulate', 'ringdown': 60.0}
    cases = [
        ('rectangular', 16.0, 0.015625, {}, 0.0, None),               # pi/2 +x
        ('rectangular', 32.0, 0.015625, {}, 0.5 * PI, None),          # pi   +y
        ('gaussian', 60.0, 0.020, {'sigma': 15.0}, 1.1, None),
        ('sinc', 80.0, 0.020, {'sigma': 40.0}, 0.0, None),
        ('WURST', 200.0, 0.020, {'n': 20.0, 'bw': 200.0}, 0.4, None),
        ('sech/tanh', 200.0, 0.020, {'b': 0.02, 'n': 1.0, 'bw': 150.0}, 0.0, None),
        ('WURST', 200.0, 0.020, {'n': 20.0, 'bw': 200.0}, 0.0, res),
    ]
    s = sd.SpinSystem((0.5,))
    for shape, tp, nu1, params, ph, r in cases:
        bx, by, bz = pex.excitation_profile(shape, tp, nu1, offsets, params,
                                            dt=0.5, phi0=ph, resonator=r)
        eng = sd.Engine(s, offsets=offsets)
        eng.run([sd.Pulse(shape=shape, tp=tp, nu1=nu1, params=params,
                          phase=ph, dt=0.5, resonator=r)])
        mx, my, mz = _bloch(eng, s)
        err = max(np.max(np.abs(mx - bx)), np.max(np.abs(my - by)),
                  np.max(np.abs(mz - bz)))
        assert err < 1e-9, "%s: engine vs Bloch mismatch %.3e" % (shape, err)
        norm = np.abs(np.sqrt(mx ** 2 + my ** 2 + mz ** 2) - 1.0).max()
        assert norm < 1e-9, "%s: |M| drifted by %.3e (unitarity)" % (shape, norm)


def test_bloch_limit_sequence():
    offsets = np.linspace(-0.1, 0.1, 101)
    tau = 137.0
    # Bloch chain: shaped pi/2(+x) - free - shaped gaussian(+y)
    M = np.tile([0.0, 0.0, 1.0], (offsets.size, 1))
    M = pex.propagate_pulse(M, 'rectangular', 16.0, 0.015625, offsets, {},
                            dt=0.5, phi0=0.0)
    M = pex.free_evolution(M, offsets, tau)
    M = pex.propagate_pulse(M, 'gaussian', 40.0, 0.025, offsets,
                            {'sigma': 10.0}, dt=0.5, phi0=0.5 * PI)
    s = sd.SpinSystem((0.5,))
    eng = sd.Engine(s, offsets=offsets)
    eng.run([
        sd.Pulse(shape='rectangular', tp=16.0, nu1=0.015625, dt=0.5),
        sd.Delay(tau),
        sd.Pulse(shape='gaussian', tp=40.0, nu1=0.025,
                 params={'sigma': 10.0}, phase=0.5 * PI, dt=0.5),
    ])
    mx, my, mz = _bloch(eng, s)
    err = max(np.max(np.abs(mx - M[:, 0])), np.max(np.abs(my - M[:, 1])),
              np.max(np.abs(mz - M[:, 2])))
    assert err < 1e-9, "sequence: engine vs Bloch mismatch %.3e" % err


# --------------------------------------------------------------------------- #
# Rung 2: Hahn echo physics
# --------------------------------------------------------------------------- #
SIGMA = 0.05                                   # Gaussian line width (GHz)


def _line():
    offs = np.linspace(-0.25, 0.25, 501)       # +-5 sigma
    return offs, sd.gaussian_weights(offs, SIGMA)


def test_hahn_echo_shape_phase_position():
    offs, w = _line()
    s = sd.SpinSystem((0.5,))
    eng = sd.Engine(s, offsets=offs, weights=w)
    tau, half = 200.0, 25.0
    win = eng.run([
        sd.Pulse(flip=0.5 * PI), sd.Delay(tau),
        sd.Pulse(flip=PI), sd.Delay(tau - half),
        sd.Detect(2 * half, 0.5),
    ])[0]
    dtt = win['t'] - 2.0 * tau
    # Exact discrete ensemble sum for the refocused pathway: V = i sum w e^{i 2pi W dt}
    expected = 1j * (w @ np.exp(2j * PI * offs[:, None] * dtt[None, :]))
    err = np.max(np.abs(win['v'] - expected))
    assert err < 1e-9, "echo vs discrete pathway sum: %.3e" % err
    # Continuum analytic shape (discretisation/truncation limited)
    analytic = 1j * np.exp(-0.5 * (2.0 * PI * SIGMA * dtt) ** 2)
    err = np.max(np.abs(win['v'] - analytic))
    assert err < 3e-3, "echo vs analytic Gaussian: %.3e" % err
    # Peak exactly at t = 2 tau, phase +y
    k = int(np.argmax(np.abs(win['v'])))
    assert abs(dtt[k]) < 1e-9, "echo peak off centre: %.3f ns" % dtt[k]
    assert abs(win['v'][k] - 1j) < 1e-3, "echo phase/amp: %r" % win['v'][k]


def test_hahn_flip_angle_scaling():
    offs, w = _line()
    s = sd.SpinSystem((0.5,))
    eng = sd.Engine(s, offsets=offs, weights=w)
    tau = 200.0

    def amp(b1, b2):
        ev = [sd.Pulse(flip=b1), sd.Delay(tau),
              sd.Pulse(flip=b2), sd.Delay(tau), sd.Detect()]
        return eng.run(ev)[0]['v'][0]

    # Tolerance is set by the truncated discrete ensemble (the +-5 sigma cut
    # leaves ~1e-8 of non-refocusing pathways undephased), not by the engine.
    ref = amp(0.5 * PI, PI)                    # ideal: i * 1
    for b2 in (PI / 3, PI / 2, 2 * PI / 3):
        got = amp(0.5 * PI, b2) / ref
        want = np.sin(0.5 * b2) ** 2
        assert abs(got - want) < 1e-6, "sin^2(b2/2): %r vs %r" % (got, want)
    for b1 in (PI / 6, PI / 4, PI / 3):
        got = amp(b1, PI) / ref
        want = np.sin(b1)
        assert abs(got - want) < 1e-6, "sin(b1): %r vs %r" % (got, want)


def test_relaxation_tm_hahn():
    s = sd.SpinSystem((0.5,))
    tau, tm = 300.0, 800.0
    ev = [sd.Pulse(flip=0.5 * PI), sd.Delay(tau),
          sd.Pulse(flip=PI), sd.Delay(tau), sd.Detect()]
    v0 = sd.Engine(s).run(ev)[0]['v'][0]
    v1 = sd.Engine(s, relaxation={'Tm': tm}).run(ev)[0]['v'][0]
    want = np.exp(-2.0 * tau / tm)
    assert abs(v1 / v0 - want) < 1e-10, "Tm decay: %r vs %r" % (v1 / v0, want)


def test_relaxation_t1_recovery():
    s = sd.SpinSystem((0.5,))
    t1 = 700.0
    eng = sd.Engine(s, relaxation={'T1': t1})
    for t in (50.0, 200.0, 1000.0, 5000.0):
        ev = [sd.Pulse(flip=PI), sd.Delay(t),
              sd.Pulse(flip=0.5 * PI), sd.Detect()]
        v = eng.run(ev)[0]['v'][0]
        want = -1j * (1.0 - 2.0 * np.exp(-t / t1))
        assert abs(v - want) < 1e-10, "T1 recovery @%g: %r vs %r" % (t, v, want)


# --------------------------------------------------------------------------- #
# Rung 3: ESEEM vs the exact Mims formulas (S = 1/2, I = 1/2, ideal pulses)
# --------------------------------------------------------------------------- #
NU_I, A_HF, B_HF = 0.0149, 0.0040, 0.0030      # GHz


def _eseem_system(b):
    s = sd.SpinSystem((0.5, 0.5))
    s.zeeman(1, NU_I)
    s.hyperfine(0, 1, A=A_HF, B=b)
    return s


def _mims_consts():
    na = np.hypot(NU_I + 0.5 * A_HF, 0.5 * B_HF)   # nu_alpha (GHz)
    nb = np.hypot(NU_I - 0.5 * A_HF, 0.5 * B_HF)   # nu_beta
    k = (B_HF * NU_I / (na * nb)) ** 2             # modulation depth
    return 2.0 * PI * na, 2.0 * PI * nb, k


def mims_2p(tau):
    wa, wb, k = _mims_consts()
    return 1.0 - 0.25 * k * (2.0 - 2.0 * np.cos(wa * tau) - 2.0 * np.cos(wb * tau)
                             + np.cos((wa + wb) * tau) + np.cos((wa - wb) * tau))


def mims_3p(tau, T):
    wa, wb, k = _mims_consts()
    return 1.0 - 0.25 * k * (
        (1.0 - np.cos(wa * tau)) * (1.0 - np.cos(wb * (tau + T)))
        + (1.0 - np.cos(wb * tau)) * (1.0 - np.cos(wa * (tau + T))))


def test_2p_eseem_mims():
    eng = sd.Engine(_eseem_system(B_HF))           # single packet, dW = 0
    ref = sd.Engine(_eseem_system(0.0))            # B = 0: unmodulated reference
    p90, p180 = sd.Pulse(flip=0.5 * PI), sd.Pulse(flip=PI)
    taus = np.arange(8.0, 600.0, 4.0)
    V = np.empty(taus.size)
    for i, tau in enumerate(taus):
        ev = [p90, sd.Delay(tau), p180, sd.Delay(tau), sd.Detect()]
        v = eng.run(ev)[0]['v'][0]
        v0 = ref.run(ev)[0]['v'][0]
        ratio = v / v0
        assert abs(ratio.imag) < 1e-9, "2p ratio not real: %r" % ratio
        V[i] = ratio.real
    err = np.max(np.abs(V - mims_2p(taus)))
    assert err < 1e-9, "2-pulse ESEEM vs Mims: %.3e" % err


# 8-step cycle isolating the single stimulated-echo pathway dp = (+1, -1, -1):
# quadrature (4-phase) on P1 separates dp1 = +1 from the mirror pathway's -1
# (which does NOT dephase on a single on-resonance packet, unlike in a broad
# line), 2-phase on P2 selects dp2 odd (i.e. p = 0 storage during T);
# receiver = -sum(dp_i * phi_i) = f2 - f1.
CYCLE_3P = [([f1, f2, 0.0], (f2 - f1) % (2.0 * PI))
            for f1 in (0.0, 0.5 * PI, PI, 1.5 * PI)
            for f2 in (0.0, PI)]


def test_3p_eseem_mims_phase_cycle():
    eng = sd.Engine(_eseem_system(B_HF))
    ref = sd.Engine(_eseem_system(0.0))
    p = [sd.Pulse(flip=0.5 * PI) for _ in range(3)]
    tau = 120.0
    Ts = np.arange(0.0, 800.0, 8.0)
    V = np.empty(Ts.size)
    Vnc = np.empty(Ts.size, dtype=complex)         # no cycle -> contaminated
    for i, T in enumerate(Ts):
        ev = [p[0], sd.Delay(tau), p[1], sd.Delay(T), p[2],
              sd.Delay(tau), sd.Detect()]
        v = eng.run(ev, phase_cycle=CYCLE_3P)[0]['v'][0]
        v0 = ref.run(ev, phase_cycle=CYCLE_3P)[0]['v'][0]
        ratio = v / v0
        assert abs(ratio.imag) < 1e-9, "3p ratio not real: %r" % ratio
        V[i] = ratio.real
        Vnc[i] = eng.run(ev)[0]['v'][0] / v0
    want = mims_3p(tau, Ts)
    err = np.max(np.abs(V - want))
    assert err < 1e-9, "3-pulse ESEEM vs Mims: %.3e" % err
    # Sanity: without the cycle the single-packet signal must NOT match Mims
    # (FID + 2-pulse-echo pathways overlap) -- proves the cycle does the work.
    assert np.max(np.abs(Vnc - want)) > 1e-3, "no-cycle run suspiciously clean"


# --------------------------------------------------------------------------- #
# Convergence / unitarity
# --------------------------------------------------------------------------- #
def test_dt_convergence():
    offsets = np.linspace(-0.15, 0.15, 101)
    s = sd.SpinSystem((0.5,))

    def mz(dt):
        eng = sd.Engine(s, offsets=offsets)
        eng.run([sd.Pulse(shape='WURST', tp=200.0, nu1=0.02,
                          params={'n': 20.0, 'bw': 200.0}, dt=dt)])
        return _bloch(eng, s)[2]

    d1 = np.max(np.abs(mz(0.5) - mz(0.25)))
    d2 = np.max(np.abs(mz(0.25) - mz(0.125)))
    assert d1 < 5e-2, "dt=0.5 already far off (%.3e)" % d1
    # Mid-step piecewise-constant propagation is 2nd order: halving dt should
    # cut the step error by ~4; allow a generous factor 2.
    assert d2 < 0.6 * d1, "no dt convergence: %.3e -> %.3e" % (d1, d2)


def test_purity_conserved():
    eng = sd.Engine(_eseem_system(B_HF))           # d = 4, eigh propagator path
    p = sd.Pulse(flip=0.5 * PI)
    eng.run([p, sd.Delay(137.0), p, sd.Delay(450.0), p,
             sd.Delay(137.0), sd.Detect(60.0, 1.0)])
    rho = eng.rho_last[0]
    purity = np.trace(rho @ rho).real
    want = np.trace(eng.sys.Sz_e @ eng.sys.Sz_e).real
    assert abs(purity - want) < 1e-10, "Tr(rho^2) drifted: %r vs %r" % (purity, want)


# --------------------------------------------------------------------------- #
TESTS = [
    test_bloch_limit_single_pulses,
    test_bloch_limit_sequence,
    test_hahn_echo_shape_phase_position,
    test_hahn_flip_angle_scaling,
    test_relaxation_tm_hahn,
    test_relaxation_t1_recovery,
    test_2p_eseem_mims,
    test_3p_eseem_mims_phase_cycle,
    test_dt_convergence,
    test_purity_conserved,
]


def main():
    failed = 0
    for fn in TESTS:
        t0 = time.time()
        try:
            fn()
            print("PASS  %-38s (%.2f s)" % (fn.__name__, time.time() - t0))
        except Exception as exc:
            failed += 1
            print("FAIL  %-38s %s" % (fn.__name__, exc))
    print("-" * 60)
    print("%d/%d passed" % (len(TESTS) - failed, len(TESTS)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
