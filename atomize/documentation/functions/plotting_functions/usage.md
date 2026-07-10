# Usage

To call plotting functions one should import general function module inside a script:

```python
import atomize.general_modules.general_functions as general
```

## 1D plotting { #1d-plotting }

```python
plot_1d('name', Xdata, Ydata, label='label', xname='NameXaxis',
        xscale='XaxisDimension', yname='NameYaxis', yscale='YaxisDimension',
        scatter='False', timeaxis='False', vline='False',
        pr='None', text='')
```

| Argument          | Description |
| ----------------- | ----------- |
| `Xdata`, `Ydata`  | numpy arrays or python lists of data |
| `name`            | String of the plot name |
| `label`           | String of the curve name |
| `text`            | Label of the plot (for multithreading only) |
| `scatter`         | `['False', 'True']`. Enables scatter plot |
| `timeaxis`        | `['False', 'True']`. Enables time axis |
| `vline`           | `'False'` or a tuple `(vline1, vline2)`. Shows up to two vertical lines |
| `pr`              | Handle for non-blocking (background) plotting — pass back the value the previous call returned (see below) |

Other arguments are optional and used for automatic scaling (i.e. V to mV, etc.). Please, note that it is impossible to redraw a line with scatters if they have the same name.

There is a possibility to draw data in the background so plotting never paces the measurement loop. Initialise a handle to `'None'`, then pass it back through the `pr` keyword on every call. The call is then **non-blocking**: the frame is handed to a persistent background worker that draws the freshest state of each plot and **coalesces per plot name** — if a frame for that name is still pending, it is replaced by the newer one, so superseded intermediate frames are skipped. The final frame is always drawn. A minimal working example for background drawing with a dynamic label is the following:

```python
import atomize.general_modules.general_functions as general
process = 'None'
for i in range(10):

    # draw one curve (x_axis, data_x) with a vertical line and a dynamic label "text"
    process = general.plot_1d('NAME_1', x_axis, data_1, xname='Delay',
        xscale='ns', yname='Area', yscale='V*s', label='curve',
        vline=(i, ), pr=process, text=str(i))

    # draw two curves (x_axis, data_x) and (x_axis, data_y) simultaneously
    process = general.plot_1d('NAME_2', x_axis, (data_1, data_2), label='curve',
        xname='Delay', xscale='ns', yname='Area', yscale='V*s',
        vline=(i, ), text=str(i))
```

A tuple `(data_1, data_2)` can be used as `Ydata`. In this case two curves will be plot simultaneously (see example above). A dynamic label based on the `text` keyword argument works only for background (`pr`) drawing. For a standard drawing mode a function [`general.text_label()`](#dynamic-labeling) should be used.

### Background plotting for a whole script { #async-plotting }

Instead of threading a `pr` handle through every call, you can switch the **whole process** to non-blocking plotting once, near the top of the script:

```python
general.set_plotting_async(True)
```

After this, every `plot_1d()` / `plot_2d()` that does not pass an explicit `pr` is handed to the background worker automatically, with the same per-name coalescing. This is what the control-center acquisition tools use so a scan runs at full speed regardless of how fast the GUI can redraw. `append_1d()` stays synchronous either way — it is incremental, so a dropped frame would drop points. A live `digitizer_get_curve()` that returns `None` (no new buffer this call) is still skipped, not queued.

!!! note "Why this matters"
    Because the plot window is one Qt process, a scan that plots faster than the GUI can paint is otherwise paced by the redraw (which is why minimising the plot window used to speed up an acquisition). Background plotting decouples the two: the measurement loop only enqueues the latest frame and moves on.

---

## 1D plotting in the test run { #1d-plotting-in-the-test-run }

```python
plot_1d_test('name', Xdata, Ydata, label='label', xname='NameXaxis',
        xscale='XaxisDimension', yname='NameYaxis', yscale='YaxisDimension',
        scatter='False', timeaxis='False', vline='False',
        pr='None', text='')
```

Same arguments and parallel-drawing semantics as [`plot_1d()`](#1d-plotting), but the curve is drawn **only when the script is launched in test mode** (i.e. when the GUI's *Test Scripts* checkbox is on, or the script is invoked as `python script.py test`). In a normal experimental run `plot_1d_test()` is a no-op and returns `None`.

Use it to inspect intermediate data — generated waveforms, computed pulse shapes, derived sequences — during the pre-flight check without cluttering plots during real acquisition. It mirrors the [`message_test()`](../general_functions/general_functions.md#print-a-string-in-the-main-window-in-the-test-run) idiom.

---

## 2D plotting { #2d-plotting }

```python
plot_2d('name', data, start_step=((Xstart, Xstep), (Ystart, Ystep)),
        xname='NameXaxis', xscale='XaxisDimension',
        yname='NameYaxis Field', yscale='YaxisDimension',
        zname='NameZaxis', zscale='ZaxisDimension',
        pr='None', text='')
```

| Argument     | Description |
| ------------ | ----------- |
| `data`       | Multidimensional numpy array; example = `[[1,1,1,..],[2,2,2,..],[3,3,3,..],..]` |
| `name`       | String of the plot name |
| `label`      | String of the curve name |
| `text`       | Label of the plot (for multithreading only) |
| `pr`         | Handle for non-blocking (background) plotting — pass back the value the previous call returned (see below) |
| `start_step` | List of starting points and steps for the X and Y axis |

Other arguments are optional and used for automatic scaling (i.e. V to mV, etc.).

`plot_2d()` supports the same non-blocking background drawing as [`plot_1d()`](#1d-plotting): initialise a handle to `'None'` and pass it back through `pr` on every call. Frames coalesce per plot name (only the freshest is drawn), so a slow GUI never paces the acquisition. A minimal working example with a dynamic label is the following:

```python
import atomize.general_modules.general_functions as general
process = 'None'
for i in range(10):

    process = general.plot_2d('NAME', data, start_step=((0, 1), (0, 1)),
        xname='Time', xscale='ns', yname='Delay', yscale='ns',
        zname='Intensity', zscale='V', pr=process, text=str(i))
```

---

## Partial 2D updates { #2d-partial-updates }

```python
update_2d('name', data, lo, hi, start_step=((Xstart, Xstep), (Ystart, Ystep)),
        xname='NameXaxis', xscale='XaxisDimension',
        yname='NameYaxis', yscale='YaxisDimension',
        zname='NameZaxis', zscale='ZaxisDimension',
        pr='None', text='')
```

| Argument     | Description |
| ------------ | ----------- |
| `data`       | The script's **live full-frame** numpy array, updated in place before each call |
| `lo`, `hi`   | Column range `[lo:hi)` along the **last axis** of `data` that changed since the previous call |
| other        | Same as [`plot_2d()`](#2d-plotting) |

`update_2d()` is the incremental counterpart of [`plot_2d()`](#2d-plotting) for acquisitions where each readout only changes a small column range of a large 2D result — most notably the [partial-range readout](../digitizer.md#digitizer_get_curve-points) of the Insys FM214x3GDA. Instead of serialising and redrawing the whole frame on every call, only the changed columns cross to the plot window; the plotter keeps the full image and patches the range in place. The per-readout plotting cost is therefore proportional to the size of the *update*, not the size of the *array*.

`data` must be the persistent array the script keeps up to date (`data[..., lo:hi] = new_columns`) — the columns are sliced out of it **at send time**. This is what makes the background (`pr`) mode safe: when several updates of one plot are pending, they coalesce into a single frame covering the **union** of their ranges, read fresh from the array, so a slow GUI drops no columns and never paces the measurement loop. On the very first call (or after the plot is closed) the plotter allocates a zero image of the full size and fills it in as updates arrive; passing `lo=0, hi=data.shape[-1]` forces a full redraw. If the full frame exceeds the [display cap](#large-data) (4 M cells), the call transparently falls back to a full `plot_2d()` so the display decimation stays correct.

A typical acquisition loop:

```python
import atomize.general_modules.general_functions as general

data = np.zeros((2, points_window, POINTS))
process = 'None'

a, b, rng = pb.digitizer_get_curve(POINTS, PHASES, current_scan=k,
                                   total_scan=SCANS, partial=True)
if a is not None:
    i0, i1 = rng
    data[0][:, i0:i1] = a
    data[1][:, i0:i1] = b
    process = general.update_2d('NAME', data, i0, i1,
        start_step=((0, 0.4), (0, STEP)), xname='Time', xscale='s',
        yname='Delay', yscale='s', zname='Intensity', zscale='mV',
        pr=process, text=f'Scan: {k}')
```

`update_2d()` honours [`set_plotting_async(True)`](#async-plotting) the same way `plot_1d()` / `plot_2d()` do. In test mode it is a no-op and returns `None`.

---

## Colormap and levels (2D) { #colormap }

The 2D image view offers a choice of colormap and levelling via the image right-click
→ **Colormap** menu. The mode is **Default** unless you pick another; it is remembered
for the rest of the run (per image dock).

| Mode | Use for |
| ---- | ------- |
| **Default** | The standard auto-levelling (data min–max on a blue–white–red map) — the original behaviour, with no extra cost. This is the default |
| **Auto** | Chooses automatically — a **sequential** (viridis) map for one-sided signals, a **bipolar** blue–white–red map for two-sided ones. The first (non-trivial) choice is *locked for the run*, so a live, dynamically re-pushed plot cannot flip colormaps mid-acquisition (it re-decides on a new dataset or when Auto is re-selected) |
| **Bipolar** | Blue–white–red diverging map |
| **Sequential** | Perceptually-uniform viridis map |

Two toggles refine the levelling in the **Auto / Bipolar / Sequential** modes:

- **Center bipolar on baseline** — pins the white of the bipolar map to the estimated
  baseline (the data median) instead of the level midpoint, so a **non-zero baseline
  reads as neutral** and the positive/negative excursions stay directly comparable even
  when they are asymmetric. Recommended for baseline-subtracted or bimodal maps.
- **Per-frame auto-levels (stacks)** — when a multi-frame stack is plotted, level and
  colour **each frame on its own statistics**, so e.g. a raw (non-zero baseline) frame
  and a baseline-subtracted frame in the same stack both display correctly. Turn it off
  to share one fixed scaling across all frames when you want them directly comparable
  (e.g. a relaxation series).

The baseline used by these modes is estimated from a subsample of the data, so enabling
them stays as fast as the default levelling even on large maps. The histogram to the
right of the image can always be dragged to set levels manually.

---

## 2D plotting in the test run { #2d-plotting-in-the-test-run }

```python
plot_2d_test('name', data, start_step=((Xstart, Xstep), (Ystart, Ystep)),
        xname='NameXaxis', xscale='XaxisDimension',
        yname='NameYaxis Field', yscale='YaxisDimension',
        zname='NameZaxis', zscale='ZaxisDimension',
        pr='None', text='')
```

Same arguments and parallel-drawing semantics as [`plot_2d()`](#2d-plotting), but the surface is drawn **only when the script is launched in test mode**. In a normal experimental run `plot_2d_test()` is a no-op and returns `None`. Use it for diagnostic 2D inspection during the pre-flight check without polluting plots during real acquisition.

---

## Large traces and maps { #large-data }

Big datasets stay responsive automatically. A 1D curve with more points than the view is wide is drawn with a peak-preserving decimation (and only the on-screen part is rasterised); a 2D image larger than the view is decimated to display resolution before the colour pass. This is **display-only** — the crosshair readout, the ruler, *Send to Data Treatment* and every saved file always see the full-resolution data. Very large payloads are additionally capped for display (2 M points for 1D, 4 M cells for 2D); a log line notes when a plot was strided, and the arrays held by the script and written to disk are never modified.

---

## Dynamic labeling { #dynamic-labeling }

```python
text_label('label', DynamicValue)
```

| Argument       | Description |
| -------------- | ----------- |
| `label`        | String |
| `DynamicValue` | Number that will change dynamically |

---

## Clearing { #clearing }

```python
plot_remove('name_of_plot')
```
