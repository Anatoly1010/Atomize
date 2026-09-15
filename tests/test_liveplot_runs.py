import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
import pytest
from PyQt6.QtCore import QObject, QItemSelectionModel, Qt
from PyQt6.QtTest import QTest
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


def test_following_shows_all_connected_sources_and_excludes_inactive_pins(liveplot):
    first, second = QObject(), QObject()
    push(liveplot, first, 'A')
    push(liveplot, first, 'B')
    assert visible(liveplot) == {'A', 'B'}
    liveplot.namelist.select_plot('A')
    liveplot.namelist.toggle_pin()
    push(liveplot, second, 'C')
    push(liveplot, second, 'D')
    assert visible(liveplot) == {'A', 'B', 'C', 'D'}
    assert not liveplot.namelist['B'].closed
    push(liveplot, first, 'B', offset=10)
    push(liveplot, first, 'Late plot')
    assert visible(liveplot) == {'A', 'B', 'C', 'D', 'Late plot'}
    np.testing.assert_array_equal(liveplot.namelist['B'].curves['signal'].yData, np.arange(5) + 10)
    liveplot.namelist.source_disconnected(first)
    assert visible(liveplot) == {'A', 'B', 'C', 'D', 'Late plot'}
    assert not liveplot.namelist.show_run_button.isChecked()
    liveplot.namelist.show_run_button.click()
    assert visible(liveplot) == {'C', 'D'}
    assert liveplot.namelist.show_run_button.isChecked()
    assert 'A' in liveplot.namelist.pinned


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
    first, second = QObject(), QObject()
    push(liveplot, first, 'Old')
    liveplot.namelist.source_disconnected(first)
    liveplot.namelist.begin_run()
    assert visible(liveplot) == set()
    assert 'Old' in liveplot.namelist
    push(liveplot, second, 'New A')
    push(liveplot, second, 'New B')
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
    plots.source_disconnected(source)
    push(liveplot, QObject(), 'C')
    assert not plots.grid_button.isChecked()
    assert plots.selection_hint.isHidden()
    assert plots.namelist_view.selectionMode() == plots.namelist_view.SelectionMode.SingleSelection
    assert visible(liveplot) == {'C'}


@pytest.mark.parametrize('grid', [False, True])
def test_show_current_run_restores_closed_plots_after_browsing(liveplot, grid):
    plots = liveplot.namelist
    assert not plots.show_run_button.isEnabled()
    assert not plots.show_run_button.isChecked()
    first, second = QObject(), QObject()
    push(liveplot, first, 'Pinned')
    plots.toggle_pin()
    push(liveplot, first, 'Old')
    push(liveplot, second, 'A')
    push(liveplot, second, 'B')
    push(liveplot, second, 'Deleted')
    del plots['Deleted']
    plots.source_disconnected(first)
    assert not plots.show_run_button.isChecked()
    liveplot.tabwidget.setCurrentIndex(1)
    liveplot.show()
    QApplication.processEvents()
    plots['A'].close_button.click()
    assert not plots.show_run_button.isChecked()
    index = plots.namelist_model.findItems('Old')[0].index()
    QTest.mouseClick(plots.namelist_view.viewport(), Qt.MouseButton.LeftButton,
                     pos=plots.namelist_view.visualRect(index).center())
    assert visible(liveplot) == {'Pinned', 'Old'}
    assert not plots.show_run_button.isChecked()
    if grid:
        QTest.mouseClick(plots.grid_button, Qt.MouseButton.LeftButton)
    push(liveplot, second, 'A', offset=40)
    QTest.mouseClick(plots.show_run_button, Qt.MouseButton.LeftButton)
    QApplication.processEvents()
    assert visible(liveplot) == {'A', 'B'}
    assert all(plots[name].isVisible() for name in ('A', 'B'))
    assert plots.show_run_button.isChecked()
    assert not plots.grid_button.isChecked()
    np.testing.assert_array_equal(plots['A'].curves['signal'].yData, np.arange(5) + 40)
    push(liveplot, second, 'C')
    assert visible(liveplot) == {'A', 'B', 'C'}
    plots['A'].close_button.click()
    push(liveplot, second, 'A', offset=50)
    assert visible(liveplot) == {'B', 'C'}
    plots.show_run_button.click()
    assert visible(liveplot) == {'A', 'B', 'C'}
    assert plots.show_run_button.isChecked()
    plots.show_run_button.click()
    assert visible(liveplot) == {'A', 'B', 'C'}
    assert plots.show_run_button.isChecked()


def test_show_current_run_restores_2d_and_tracks_run_boundaries(liveplot):
    plots = liveplot.namelist
    source = QObject()
    push(liveplot, source, 'Trace')
    data = np.arange(20).reshape(4, 5)
    liveplot.meta = dict(operation='plot_z', name='Image', rank=2, start_step=None,
                         Xname='X', X='', Yname='Y', Y='', Zname='Z', Z='', value='')
    liveplot.do_operation(data, source=source)
    plots['Image'].close_button.click()
    plots['Trace'].close_button.click()
    assert visible(liveplot) == set()
    plots.show_run_button.click()
    assert visible(liveplot) == {'Trace', 'Image'}
    np.testing.assert_array_equal(plots['Image'].get_data(), data)
    plots.source_disconnected(source)
    assert visible(liveplot) == {'Trace', 'Image'}
    assert not plots.show_run_button.isChecked()
    assert not plots.show_run_button.isEnabled()
    plots.show_run_button.click()
    assert visible(liveplot) == {'Trace', 'Image'}
    plots.begin_run()
    assert not plots.show_run_button.isEnabled()
    plots.show_run_button.click()
    assert visible(liveplot) == set()
    push(liveplot, QObject(), 'Next')
    plots['Next'].close_button.click()
    plots.show_run_button.click()
    assert visible(liveplot) == {'Next'}
    del plots['Next']
    assert not plots.show_run_button.isEnabled()


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


@pytest.mark.parametrize('grid', [False, True])
def test_disconnection_preserves_manual_browsing(liveplot, grid):
    plots = liveplot.namelist
    first, second = QObject(), QObject()
    push(liveplot, first, 'Old')
    plots.source_disconnected(first)
    push(liveplot, second, 'Live')
    plots.select_plot('Old')
    plots.activate_item(plots.namelist_model.findItems('Old')[0].index())
    plots.grid_button.setChecked(grid)
    assert visible(liveplot) == {'Old'}
    assert not plots.show_run_button.isChecked()
    plots.source_disconnected(second)
    assert visible(liveplot) == {'Old'}
    assert not plots.show_run_button.isEnabled()
    plots.show_run_button.click()
    assert visible(liveplot) == {'Old'}


def test_data_updates_do_not_rearrange_or_reopen_hidden_plots(liveplot, monkeypatch):
    plots = liveplot.namelist
    source = QObject()
    push(liveplot, source, 'A')
    push(liveplot, source, 'B')
    plots['A'].close_button.click()
    refreshes = []
    refresh_view = plots.refresh_view

    def record_refresh(*args):
        refreshes.append(True)
        refresh_view(*args)

    monkeypatch.setattr(plots, 'refresh_view', record_refresh)
    push(liveplot, source, 'A', offset=10)
    push(liveplot, source, 'B', offset=20)
    assert not refreshes
    assert visible(liveplot) == {'B'}
    np.testing.assert_array_equal(plots['A'].curves['signal'].yData, np.arange(5) + 10)
    np.testing.assert_array_equal(plots['B'].curves['signal'].yData, np.arange(5) + 20)


def test_shared_plot_stays_active_until_all_sources_disconnect(liveplot):
    first, second = QObject(), QObject()
    plots = liveplot.namelist
    push(liveplot, first, 'Dig')
    push(liveplot, second, 'Dig')
    item = plots.namelist_model.findItems('Dig')[0]
    plots.source_disconnected(first)
    assert not item.icon().isNull()
    assert plots.show_run_button.isEnabled()
    assert plots.show_run_button.isChecked()
    assert visible(liveplot) == {'Dig'}
    plots.source_disconnected(second)
    assert item.icon().isNull()
    assert not plots.show_run_button.isEnabled()
    assert not plots.show_run_button.isChecked()
    assert visible(liveplot) == {'Dig'}
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
