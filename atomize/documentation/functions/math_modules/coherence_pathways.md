# Coherence Pathways & Phase Cycling

Two pure-Python helpers for designing and checking pulse-EPR phase cycles —
**no NumPy/scipy, no hardware** — just integer coherence-order bookkeeping.

- `expand_phase_cycling()` turns compact phase-cycle notation into the explicit
  per-step phase of every pulse plus the matching receiver phase.
- `analyze_pathways()` enumerates every coherence transfer pathway, decides which
  the phase cycle **keeps** and which it **phases out**, locates each surviving
  echo, and flags the FIDs.

```python
import atomize.math_modules.coherence_pathways as coh
```

## Background

A **coherence transfer pathway** is the list of electron coherence orders
$p \in \{-1, 0, +1\}$ during each inter-pulse delay, starting from equilibrium
($p = 0$) and ending at the detected order $-1$. An $n$-pulse sequence therefore
has $3^{\,n-1}$ pathways. When a pulse phase is shifted by $\varphi$, a pathway
with coherence-order change $\Delta p$ at that pulse acquires a phase
$-\Delta p\,\varphi$. Co-adding over the steps of a phase cycle, a pathway
**survives** iff its total acquired phase $-\sum_i \Delta p_i\,\varphi_i$ tracks
the receiver phase at every step; otherwise the steps cancel and it is
**suppressed**. The desired pathway survives by construction — anything else that
survives is an artefact the cycle fails to remove.

An echo forms where the offset-dependent phase $\sum_k p_k\,\tau_k$ over the
sequence vanishes, i.e. at $t_\text{last pulse} + \sum_k p_k\,\tau_k$. An **FID**
is the special pathway that becomes observable at one pulse and is never
refocused ($p = 0$ until pulse $j$, then $-1$ onward), so its "echo" sits exactly
on pulse $j$ and decays from there. For a Hahn echo this is how the $\pi$-pulse
FID shows up — and the 2-step cycle removes it.

!!! info "Method & references"
    The enumeration / selection follows Stoll & Kasumaj,
    *Appl. Magn. Reson.* **35**, 15 (2008), and the DEER artefact analysis of
    Spindler / Prisner *et al.*, *Phys. Chem. Chem. Phys.* **18**, 17223 (2016).

!!! warning "Selection rule, not amplitudes"
    This is a **bookkeeping** tool. It lists which pathways the phase cycle lets
    through, **not** their intensities. Selection depends only on $\Delta p$, so
    it is exact for real (non-ideal) pulses — but whether a surviving pathway is
    actually excited, and how strongly, depends on pulse flip angle / bandwidth /
    resonator / offset and is **not** modelled here. Relaxation and nuclear
    coherences (ESEEM/HYSCORE modulation amplitudes) are out of scope; electron
    coherence orders are restricted to $-1/0/+1$ ($S = 1/2$).

## Notation

| Token | Meaning |
| ----- | ------- |
| `+x` `+y` `-x` `-y` (or `x` `y` `-x` `-y`) | a fixed phase |
| `x,y,-x` | an explicit, comma-separated cycle |
| `(x)` | a nested **2-step** cycle (180° steps) |
| `[x]` | a nested **4-step** cycle (90° quadrature) |
| `'-1,2'` (receiver only) | per-pulse **coherence-order coefficients**; the receiver phase is derived automatically |

## `expand_phase_cycling(recv, *pulse_phases)` { #expand_phase_cycling }

Expand the short notation into explicit per-step lists.

```python
coh.expand_phase_cycling('-1,2', '(x)', 'x')
# {'pulses': [['+x', '-x'], ['+x', '+x']], 'receiver': ['+x', '-x']}
```

Returns `{"pulses": [[phase per step] per pulse], "receiver": [phase per step]}`.

## `analyze_pathways(recv, pulse_phases, positions, det_pos)` { #analyze_pathways }

Enumerate and classify the pathways.

| Argument | Description |
| -------- | ----------- |
| `recv` | receiver spec — usually the coefficient string, e.g. `'-1,2'` (Hahn), `'1,-2,0,2'` (4p-DEER) |
| `pulse_phases` | list of per-pulse phase notations, in order (e.g. `['(x)', 'x']`) |
| `positions` | absolute start position of each pulse (see [`positions_from_taus`](#positions_from_taus)) |
| `det_pos` | absolute position of the detection window |

Returns a dict:

| Key | Meaning |
| --- | ------- |
| `total` | number of pathways, $3^{\,n-1}$ |
| `steps` | number of phase-cycle steps |
| `suppressed` | count of pathways the cycle removes |
| `survivors` | list of `{p, dp, echo, desired, fid, role}` — `p` is the per-delay orders (detection last), `desired` is True when the echo lands on the window, `fid` is the pulse number when the pathway is that pulse's FID, `role` a label |
| `fids` | per-pulse FID table: `{pulse, echo, survives}` for **every** pulse, kept or removed |

```python
import atomize.math_modules.coherence_pathways as coh
import atomize.general_modules.general_functions as general

pos = coh.positions_from_taus([288], grid=3.2)      # -> [0.0, 288.0]
an  = coh.analyze_pathways('-1,2', ['(x)', 'x'], pos, det_pos=576.0)

general.message('%d survive, %d phased out' % (len(an['survivors']), an['suppressed']))
for f in an['fids']:
    general.message('P%d FID -> %s' % (f['pulse'], 'kept' if f['survives'] else 'phased out'))
# P1 FID -> kept ; P2 (pi-pulse) FID -> phased out
```

## `pathway_report(recv, pulse_phases, positions, det_pos)` { #pathway_report }

A ready-to-print multi-line summary — the survivor table, the per-pulse FID
table, and the caveat — for `print` or `general.message(...)`.

```python
print(coh.pathway_report('1,-2,0,2', ['(x)', 'x', '[x]', 'x'],
                         [0.0, 208.0, 320.0, 1936.0], 3456.0))
```

```
Coherence transfer pathways  (electron p in -1,0,+1; detection -1)
  27 pathways, 8-step cycle  ->  6 survive, 21 phased out
  pathway (per delay, detection last) | echo | role
  ----------------------------------------------------
  -++-         |    3456.0 | DETECTED (echo on window)
  ----         |       0.0 | FID from P1
  +---         |     416.0 | artefact echo (-3040.0 off window)
  -00-         |    1728.0 | artefact echo (-1728.0 off window)
  +00-         |    2144.0 | artefact echo (-1312.0 off window)
  +++-         |    3872.0 | artefact echo (+416.0 off window)
  ...
```

The five surviving artefacts here are exactly the unsuppressed DEER echoes
discussed by Prisner *et al.* — useful for spotting one that overlaps the
detection window.

## `positions_from_taus(taus, base=0.0, grid=None)` { #positions_from_taus }

Cumulative absolute pulse positions from inter-pulse delays: the first pulse at
`base`, each next one `+tau` later. With `grid` set, positions snap **up** to
that raster (matching hardware timing); leave it `None` for exact values.

```python
coh.positions_from_taus([1000, 200])            # [0.0, 1000.0, 1200.0]
coh.positions_from_taus([200], grid=3.2)        # [0.0, 201.6]  (ceil to grid)
```
