# Plotting Functions

## General information

Plotting of raw experimental data is available via [Liveplot](https://github.com/PhilReinhold/liveplot) library modified according to the aims of the project. The general idea of the Liveplot is a possibility to see your data as it comes in to your script, with minimal effort using an appropriate shell to cover verbose syntax.

The [Liveplot](https://github.com/PhilReinhold/liveplot) provides several possibilities for plotting 1D and 2D data. For raw experimental data plotting mainly four of them are applicable. An additional customizability has been added to these functions in comparison with the original Liveplot library. The functions are the following:

| Function | Description |
| -------- | ----------- |
| [`plot_1d(*args, **kargs)`](usage.md#1d-plotting)             | 1D plot |
| [`plot_1d_test(*args, **kargs)`](usage.md#1d-plotting-in-the-test-run)             | 1D plot in the test run |
| [`plot_2d(*args, **kargs)`](usage.md#2d-plotting)             | 2D plot |
| [`plot_2d_test(*args, **kargs)`](usage.md#2d-plotting-in-the-test-run)             | 2D plot in the test run |
| [`text_label('label', DynamicValue)`](usage.md#dynamic-labeling) | Dynamic plot label |
| [`plot_remove('name_of_plot')`](usage.md#clearing)            | Clear a plot |

## GUI features

### Current Plots dock

Right-click in the Current Plots dock area to access:

| Action | Result |
| ------ | ------ |
| Delete dock         | Remove the selected dock with graphs |
| Open 1D CSV         | Open multi-column CSV data and plot it in a new graph dock |
| Open 2D CSV         | Open 2D CSV data and plot it in a new graph dock |

### Graph docks — mouse / keyboard

| Action | Result |
| ------ | ------ |
| Middle-click curve name in legend  | Remove the curve from the graph |
| Left-click curve name in legend    | Bring the curve to the top layer |
| Drag a curve                       | Shift it vertically or horizontally |
| `Ctrl` + drag a curve              | Scale it vertically |
| `Alt` + Left-click a curve         | Reset its shift and scale to original values |
| Double-click                       | Show/hide cross-hair (1D) or cross-section (2D) widget |
| Middle-click                       | Lock the cross-hair or cross-section widget in its current position |
| `Shift` + left-drag                | Ruler — measure distance between two points (snapped) |
| `Shift` + `Ctrl` + left-drag       | Ruler with free coordinates (no snapping) |

**Ruler details:** For 1D plots the endpoints snap to the nearest data point of the curve under the press position, and the ruler adopts that curve's color; the label shows ΔX, ΔY, and the (X, Y) of both endpoints. For 2D plots the endpoints snap to the nearest pixel center, and the label shows ΔX, ΔY, ΔZ, and the (X, Y, Z) of both endpoints. The ruler is removed automatically when the cross-hair or cross-section widget is hidden.

### Graph dock right-click menu

| Action | Result |
| ------ | ------ |
| Import Data  | Open 1D data in multi-column CSV format and plot it directly in the graph dock |
| Export Data  | Save 2D data from the displayed contour plot |
| Hide Label   | Toggle the visibility of labels on the cross-hair or cross-section widgets |
| Clear Ruler  | Remove the current ruler overlay from the 1D or 2D plot |
