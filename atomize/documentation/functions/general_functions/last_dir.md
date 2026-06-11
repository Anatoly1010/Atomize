# Last opened directory

Every file **open** and **save** dialog in the Atomize GUI reopens in the folder
you last used, instead of always jumping back to the configured default. The
folder is remembered **per category** and **survives a relaunch**, so the script
picker, the data loader and (on the EPR endstation) each preset tool each keep
their own working directory.

## Why this is needed

Atomize runs as several independent Qt processes — the main window plus, on the
EPR endstation, each control-center tool in its own `QProcess`. A plain
`QFileDialog` has no memory of its own across processes or restarts, and the
config only provides a single static `open_dir` / `script_dir`. Without help,
every dialog opens in that one configured folder, even after you have navigated
somewhere else.

The `last_dir` helper gives each *category* of dialog a small persistent note of
the last directory the user actually browsed to, shared by every dialog in that
category and reloaded on the next launch.

## Categories

Two categories exist in every build:

| Key | Used by | Remembers |
| --- | ------- | --------- |
| `script` | the experimental-script **Open** / **Save** dialogs | your scripts folder |
| `data`   | the 1D / 2D (and, on the endstation, TR) data-open dialogs, including the *Open 1D Data* item in the pyqtgraph plot menu | your data folder |

The **EPR endstation** build adds one category per preset tool, so each remembers
its own folder independently:

| Key | Tool | File type |
| --- | ---- | --------- |
| `cw` | CW EPR control | `*.cw` |
| `tr` | TR EPR control | `*.tr` |
| `tune` | resonator tune preset | `*.tn` |
| `phase` | RECT phasing | `*.phase` |
| `phase_awg` | AWG phasing | `*.phase_awg` |
| `phase_cor` | phase correction | `*.csv` |

The first time a category is used (no note yet) the dialog falls back to the
configured `open_dir` / `script_dir`; from then on it opens where you left off.

## Where it is stored

Each category keeps its directory in a one-line text file named
`<key>_lastdir.txt`:

- **plain Atomize** — under the per-user config directory
  (`platformdirs.user_config_dir("atomize-py")/lastdir/`), the same place the
  copied configs live;
- **EPR endstation build** — under the repo's `libs/` runtime directory, next to
  the other runtime-IPC files (these files are git-ignored).

A note is rewritten every time a file is successfully opened **or** saved, so
saving a preset into a new folder also moves the next open there. A stale note
(folder deleted) is ignored and the configured default is used again.

## Using it from a module

Module authors wire a dialog into the memory with two calls. Load the remembered
directory when building the dialog (passing the config value as the fallback),
and save it back in the handler once a file is chosen:

```python
import atomize.general_modules.last_dir as ldir

# when opening the dialog — start where the user left off, else the config default
filedialog = QFileDialog(self, 'Open File',
                         directory=ldir.load('data', self.open_dir),
                         filter="CSV (*.csv)")
...

# in the slot that receives the chosen file — remember its folder
def open_file(self, filename):
    self.open_dir = os.path.dirname(filename)
    ldir.save('data', self.open_dir)
    ...
```

### API

`load(key, default='')`
:   Return the remembered directory for `key`, or `default` if nothing is stored
    yet or the stored path no longer exists. Never raises.

`save(key, path)`
:   Remember `path` (or its parent directory if `path` is a file) under `key`.
    Creates the storage location on first use. Never raises.

Pick a new `key` per logical category of dialog; dialogs that should share one
working folder simply pass the same key.
