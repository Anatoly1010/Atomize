# Examples

## 1D plotting

```python
import numpy as np
import atomize.general_modules.general_functions as general

xs = np.array([])
ys = np.array([])

for i in range(40):
    xs = np.append(xs, i)
    ys = np.append(ys, np.random.random_integers(0, 10))
    general.plot_1d('1D test plot', xs, ys, label='random data')
    general.wait('200 ms')
```

---

## 2D plotting

```python
import numpy as np
import atomize.general_modules.general_functions as general

data = []
step = 10
i = 0

while i <= 20:
    i = i + 1

    axis_x = np.arange(4000)
    ch_time = np.random.randint(250, 500, 1)
    zs = 1 + 100*np.exp(-axis_x/ch_time) + 7*np.random.normal(size=(4000))

    data.append(zs)

    general.wait('100 ms')

    general.plot_2d('2D test plot', data,
        start_step=((0, 1), (0.3, 0.001)),
        xname='Time', xscale='s',
        yname='Magnetic Field', yscale='T',
        zname='Intensity', zscale='V')

    general.text_label('2D test plot; step: ', i)
```
