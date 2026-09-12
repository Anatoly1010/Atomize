import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
import pytest
from PyQt6.QtCore import QObject, QItemSelectionModel
from PyQt6.QtWidgets import QApplication, QMainWindow

from atomize.main.main_window import MainWindow
from atomize.main import local_config as lconf


@pytest.fixture
def liveplot(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    monkeypatch.setattr(lconf, 'load_scripts', lambda path: str(tmp_path))
    app = QApplication.instance() or QApplication([])
    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)
    window.design_setting()
    window.insert_dock_right = True
    yield window
    for name in list(window.namelist.keys()):
        del window.namelist[name]
    window.deleteLater()
    app.processEvents()


def push(window, source, name, offset=0):
    window.meta = dict(operation='plot_y', name=name, rank=1, start_step=None, label='signal')
    window.do_operation(np.arange(5) + offset, source=source)


def visible(window):
    return {name for name, plot in window.namelist.plot_dict.items()
            if plot.area is window.dockarea and not plot.closed}


def test_new_run_replaces_previous_group_and_keeps_pinned(liveplot):
    first, second = QObject(), QObject()
    push(liveplot, first, 'A')
    push(liveplot, first, 'B')
    assert visible(liveplot) == {'A', 'B'}
    liveplot.namelist.select_plot('A')
    liveplot.namelist.toggle_pin()
    push(liveplot, second, 'C')
    push(liveplot, second, 'D')
    assert visible(liveplot) == {'A', 'C', 'D'}
    assert not liveplot.namelist['B'].closed
    push(liveplot, first, 'B', offset=10)
    push(liveplot, first, 'Late plot')
    assert visible(liveplot) == {'A', 'C', 'D'}
    np.testing.assert_array_equal(liveplot.namelist['B'].curves['signal'].yData, np.arange(5) + 10)


def test_reused_names_reopen_once_without_overriding_manual_selection(liveplot):
    first, second = QObject(), QObject()
    push(liveplot, first, 'A')
    plot = liveplot.namelist['A']
    plot.close_button.click()
    push(liveplot, second, 'A', offset=20)
    push(liveplot, second, 'B')
    assert liveplot.namelist['A'] is plot
    assert visible(liveplot) == {'A', 'B'}
    liveplot.namelist.grid_button.setChecked(True)
    index = liveplot.namelist.namelist_model.findItems('A')[0].index()
    liveplot.namelist.namelist_view.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Deselect)
    push(liveplot, second, 'A', offset=30)
    assert visible(liveplot) == {'B'}
    np.testing.assert_array_equal(plot.curves['signal'].yData, np.arange(5) + 30)


def test_run_start_hides_old_plots_before_first_data(liveplot):
    push(liveplot, QObject(), 'Old')
    liveplot.namelist.begin_run()
    assert visible(liveplot) == set()
    assert 'Old' in liveplot.namelist
    push(liveplot, None, 'New A')
    push(liveplot, None, 'New B')
    assert visible(liveplot) == {'New A', 'New B'}


@pytest.mark.parametrize('grid', [False, True])
def test_run_resets_grid_mode_and_hidden_plot_keeps_updating(liveplot, grid):
    plots = liveplot.namelist
    plots.grid_button.setChecked(grid)
    source = QObject()
    push(liveplot, source, 'A')
    push(liveplot, source, 'B')
    assert not plots.grid_button.isChecked()
    assert plots.selection_hint.isHidden()
    assert plots.namelist_view.selectionMode() == plots.namelist_view.SelectionMode.SingleSelection
    assert visible(liveplot) == {'A', 'B'}
    plots.grid_button.setChecked(grid)
    plots['A'].close_button.click()
    push(liveplot, source, 'A', offset=40)
    assert plots.grid_button.isChecked() == grid
    assert visible(liveplot) == {'B'}
    np.testing.assert_array_equal(plots['A'].curves['signal'].yData, np.arange(5) + 40)
    plots.activate_item(plots.namelist_model.findItems('A')[0].index())
    assert visible(liveplot) == {'A', 'B'}
    push(liveplot, QObject(), 'C')
    assert not plots.grid_button.isChecked()
    assert plots.selection_hint.isHidden()
    assert plots.namelist_view.selectionMode() == plots.namelist_view.SelectionMode.SingleSelection
    assert visible(liveplot) == {'C'}


def test_activity_survives_hiding_and_clears_when_source_disconnects(liveplot):
    source = QObject()
    plots = liveplot.namelist
    push(liveplot, source, 'Dig')
    item = plots.namelist_model.findItems('Dig')[0]
    assert not item.icon().isNull()
    assert 'Live source connected' in item.toolTip()
    assert 'Last data:' in item.toolTip()
    plots['Dig'].close_button.click()
    plots.begin_run()
    plots.refresh_view()
    assert not item.icon().isNull()
    plots.source_disconnected(source)
    assert item.icon().isNull()
    assert 'Source disconnected' in item.toolTip()
    assert 'Last data:' in item.toolTip()


def test_shared_plot_stays_active_until_all_sources_disconnect(liveplot):
    first, second = QObject(), QObject()
    plots = liveplot.namelist
    push(liveplot, first, 'Dig')
    push(liveplot, second, 'Dig')
    item = plots.namelist_model.findItems('Dig')[0]
    plots.source_disconnected(first)
    assert not item.icon().isNull()
    plots.source_disconnected(second)
    assert item.icon().isNull()
    del plots['Dig']
    assert 'Dig' not in plots.plot_sources
    assert 'Dig' not in plots.last_plot_update


@pytest.mark.parametrize('rank', [1, 2])
def test_header_auto_range_button_restores_scale(liveplot, rank):
    plot = liveplot.add_new_plot(rank, 'Scale test')
    if rank == 1:
        plot.plot(np.arange(10), np.arange(10), name='signal', scatter='False')
        item = plot.plot_widget.getPlotItem()
    else:
        plot.setImage(np.arange(100).reshape(10, 10), axes={'y': 0, 'x': 1})
        item = plot.plot_item
    liveplot.tabwidget.setCurrentIndex(1)
    liveplot.show()
    QApplication.processEvents()
    item.setRange(xRange=(2, 3), yRange=(2, 3))
    assert not any(item.vb.autoRangeEnabled())
    plot.auto_range_button.click()
    QApplication.processEvents()
    assert all(item.vb.autoRangeEnabled())
    assert item.buttonsHidden
    assert not item.autoBtn.isVisible()
    assert plot.auto_range_button.isVisible()
    assert plot.auto_range_button.x() + plot.auto_range_button.width() < plot.close_button.x()
