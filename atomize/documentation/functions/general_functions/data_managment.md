# Data Management

To open or save raw experimental data one can use a special module. To call functions from the module one should create a corresponding class instance.

```python
import atomize.general_modules.csv_opener_saver as openfile
file_handler = openfile.Saver_Opener()
```

Alternatively, it is possible to use the CSV Exporter embedded into Pyqtgraph for saving 1D data and a special option in Liveplot (right click → Save Data Action) for saving 2D data as comma separated two dimensional numpy array.

Every function below works with comma separated files and with HDF5 files; the format is chosen by the extension of the path, `.h5` meaning HDF5 and anything else meaning CSV. See [HDF5 files](#hdf5-files) for the layout and for when it is worth using.

## Functions

### open_1d(file_path, header=0) { #open_1d data-toc-label="open_1d" }

```python
open_1d(file_path, header=0)    # -> (data_header, numpy.array)
```

Simple function to open a specified file with comma separated values. An `.h5` file is read through the same function and returns the stored array transposed in exactly the same way, so a file saved from `np.c_[x_axis, data_x, data_y]` comes back as three rows whichever format it was written in.

| Argument    | Description |
| ----------- | ----------- |
| `file_path` | Path to file |
| `header`    | Integer specifying the number of columns in the file header |

---

### open_2d(file_path, header=0) { #open_2d data-toc-label="open_2d" }

```python
open_2d(file_path, header=0)    # -> (data_header, numpy.array)
```

Simple function to open a specified file with 2D array of comma separated values. An `.h5` file that holds both quadratures returns them stacked as a single `(2, npoints, nsamples)` array instead of the two separate matrices the CSV path keeps in two files; an `.h5` file with one matrix returns that matrix, exactly as CSV does.

| Argument    | Description |
| ----------- | ----------- |
| `file_path` | Path to file |
| `header`    | Integer specifying the number of columns in the file header |

---

### open_2d_appended(file_path, header=0, chunk_size=1) { #open_2d_appended data-toc-label="open_2d_appended" }

```python
open_2d_appended(file_path, header=0, chunk_size=1)    # -> (data_header, numpy.array)
```

This function opens a file with a single column array of values from 2D array. For an `.h5` file written with per-scan snapshots the list of slices of its `scans` dataset is returned and `chunk_size` is ignored, since the file already knows where one scan ends and the next begins.

| Argument     | Description |
| ------------ | ----------- |
| `file_path`  | Path to file |
| `header`     | Integer specifying the number of columns in the file header |
| `chunk_size` | Y axis size of the initial 2D array |

---

### open_file_dialog(directory='') { #open_file_dialog data-toc-label="open_file_dialog" }

```python
open_file_dialog(directory='')    # -> path to file.csv
```

This function returns the path to the file selected in the dialog box that opens.

| Argument    | Description |
| ----------- | ----------- |
| `directory` | Path to preopened directory in the dialog window |

---

### create_file_dialog(directory='', fmt='csv') { #create_file_dialog data-toc-label="create_file_dialog" }

```python
create_file_dialog(directory='', fmt='csv')    # -> path to file.csv
```

This function returns the path to the file specified in the dialog box that opens. It can be used to manually save your data inside the experimental script to specified file.

| Argument    | Description |
| ----------- | ----------- |
| `directory` | Path to preopened directory in the dialog window |
| `fmt`       | Extension offered by the dialog and appended to a name typed without one; `'h5'` to save HDF5 |

---

### create_file_parameters(add_name, directory='') { #create_file_parameters data-toc-label="create_file_parameters" }

```python
# returns two paths: file with add_name extension and file.csv
create_file_parameters('.param')
```

This function has the full functionality of the [`create_file_dialog()`](#create_file_dialog) function, but also returns a second file for saving parameters / header.

| Argument    | Description |
| ----------- | ----------- |
| `add_name`  | String that will be added to the second file instead of `'.csv'` extension. Example: `create_file_parameters('.param')` will create a second file with `.param` extension |
| `directory` | Path to preopened directory in the dialog window |

---

### save_header(file_path, header='', mode='w') { #save_header data-toc-label="save_header" }

```python
save_header(file_path, header='', mode='w')
```

This function saves the string given by argument `header` to the file with the path `file_path`. Argument `mode` allows choosing whether the file will be rewritten (`mode='w'`) or the data will be appended to the end of the file (`mode='a'`). For an `.h5` file the header becomes the file attribute described in [HDF5 files](#hdf5-files) and no datasets are created yet, so a run that crashes before saving still leaves its header behind.

---

### save_data(file_path, data, header='', mode='w', axes=None, fmt='%.6e', dtype=None) { #save_data data-toc-label="save_data" }

```python
save_data(file_path, data, header='', mode='w', axes=None, fmt='%.6e', dtype=None)
```

This function saves the numpy array given by the argument `data` and the string given by argument `header` to the file with the path `file_path`. Argument `mode` allows choosing whether the file will be rewritten (`mode='w'`) or the data will be appended to the end of the file (`mode='a'`).

This function works for 1D, 2D, and 3D data. In case of 3D (an array of 2D arrays) data, a separate file will be created for each 2D array with the additional `_i` string in the `file_path`; an `.h5` file keeps the first two of them as the `I` and `Q` datasets of one file instead. The standard combination of function to save the experimental data together with a header is the following:

```python
file_data, file_param = file_handler.create_file_parameters('.param')
header = 'Test Header'
file_handler.save_header(file_param, header=header, mode='w')
# Acquiring experimental data
file_handler.save_data(file_data, data, header=header, mode='w')
```

| Argument | Description |
| -------- | ----------- |
| `axes`   | `(t, sweep)` pair of 1D arrays written as the axis datasets of an `.h5` file; ignored for CSV |
| `fmt`    | Number format of the CSV columns; it also picks the HDF5 precision unless `dtype` is given |
| `dtype`  | HDF5 data type; `None` derives it from `fmt`, so `'%.6e'` (7 significant digits) gives `float32` and anything wider gives `float64`. Pass `'float64'` to store the array exactly whatever the CSV format is |

---

## HDF5 files

A path ending in `.h5` is written as a single HDF5 file instead of comma separated text. It is worth doing for the full 2D arrays of an experiment: such a file is about three times smaller than the same data as text, is written in a fraction of the time, keeps both quadratures and the axes together, and is read by Origin, MATLAB and `h5dump` without any Atomize code. Small 1D result files gain nothing from it and are kept as CSV by every control center window, but the functions accept them at any rank, so an experimental script may use them freely.

```
example_2d.h5
├── attrs
│   ├── header          str   exact header text as passed to save_data (no '# ')
│   ├── format_version  int   1
│   └── source          str   'atomize'
├── I      float32  (npoints, nsamples)   same orientation as the CSV rows
├── Q      float32  (npoints, nsamples)   only when the source has a quadrature
├── t      float64  (nsamples,)           within-trace axis
└── sweep  float64  (npoints,)            tau / field / amplitude axis
```

The array is stored exactly as `np.savetxt()` would lay it out, so a 1D file is the same layout with one axis fewer and no separate concept: `save_data()` never has to guess what the array means, and `open_1d()` / `open_2d()` differ for HDF5 exactly as they differ for CSV. The `t` and `sweep` datasets are written only when `axes` is passed. A file written with per-scan snapshots carries one more dataset, `scans`, whose first axis is the scan number and whose slice `j - 1` is the cumulative average after scan `j`.

!!! note
    The default `float32` is not a loss against CSV: the default `'%.6e'` format writes 7 significant digits, which is the same precision band. Save with `dtype='float64'` (or a wider `fmt`) if a particular array needs more.

---

## Standard numpy savetxt() function

```python
np.savetxt(path_to_file, data_to_save, fmt='%.4e', delimiter=' ',
           newline='n', header='field: %d' % i, footer='',
           comments='#', encoding=None)
```

For saving inside the script by [`create_file_dialog()`](#create_file_dialog) a standard numpy function should be used.

