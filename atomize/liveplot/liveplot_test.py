import inspect
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSpinBox, QHBoxLayout, QLabel, QPushButton, \
    QPlainTextEdit, QProgressBar
import numpy as np
import sys
import signal
from liveplot import LivePlotClient

def test_plot_y():
    for i in range(100):
        xs = np.linspace(0, 10, 100) + i / 2.
        s_arr = np.sin(xs)
        c_arr = np.cos(xs)
        c.plot_y('scrolling sine', s_arr, start_step=(xs[0], xs[1]-xs[0]), label='sin')
        c.plot_y('scrolling sine', c_arr, start_step=(xs[0], xs[1]-xs[0]), label='cos')
        yield

def test_plot_xy():
    xs = np.linspace(-1, 1, 100)
    for mu in xs:
        ys_r = np.exp((-(xs - mu)**2)/.1)
        ys_l = np.exp((-(xs + mu)**2)/.1)
        c.plot_xy('travelling packet', xs, ys_r, label='right')
        c.plot_xy('travelling packet', xs, ys_l, label='left')
        yield

def test_append_y():
    xs = np.linspace(0, 6, 100)
    for val in np.exp(xs):
        c.append_y('appending exp', val, start_step=(xs[0], xs[1]-xs[0]), label='up')
        c.append_y('appending exp', -val, start_step=(xs[0], xs[1]-xs[0]), label='down')
        yield

def test_plot_xy_parametric():
    for i in range(100):
        ts = np.linspace(0, 20, 300) + i/20.
        xs = ts**2 * np.sin(ts)
        ys = ts**2 * np.cos(ts)
        c.plot_xy('rotating spiral', xs, ys, label='a')
        c.plot_xy('rotating spiral', ys, xs, label='b')
        yield

def test_append_xy():
    c.clear('spiral out')
    ts = np.linspace(0, 20, 100)
    xs = ts**2 * np.sin(ts)
    ys = ts**2 * np.cos(ts)
    for x, y in zip(xs, ys):
        c.append_xy('spiral out', x, y, label='a')
        c.append_xy('spiral out', y, x, label='b')
        yield

def test_plot_z():
    xs, ys = np.mgrid[-500:500, -500:500]/100.
    rs = np.sqrt(xs**2 + ys**2)
    for i in range(100):
        c.plot_z('sinc', np.sinc(rs + i/20.), extent=((-5, 5), (-10, 10)))
        yield

def test_plot_huge():
    xs, ys = np.mgrid[-1500:1500, -1500:1500]/1000.
    z = np.sqrt(xs**2 + ys**2)
    c.plot_z('huge image', z, extent=((-5, 5), (-10, 10)))
    yield

def test_append_z():
    c.clear('appending sinc')
    xs, ys = np.mgrid[-100:100, -100:100]/20.
    rs = np.sqrt(xs**2 + ys**2)
    zs = np.sinc(rs)
    for i in range(200):
        c.append_z('appending sinc', zs[:,i])
        yield

def test_label():
    c.clear('label test')
    xs, ys = np.mgrid[-100:100, -100:100]/20.
    rs = np.sqrt(xs**2 + ys**2)
    zs = np.sinc(rs)
    for i in range(200):
        c.append_z('label test', zs[:,i])
        c.label('label test', 'step: %d' % i)
        yield


class TestWindow(QWidget):
    def __init__(self):
        super(TestWindow, self).__init__()
        self.setWindowTitle("LivePlot Example Runner")
        layout = QHBoxLayout(self)
        button_layout = QVBoxLayout()
        time_layout = QHBoxLayout()
        time_spin = QSpinBox()
        self.timer = QTimer()
        time_spin.valueChanged.connect(self.timer.setInterval)
        self.timer.timeout.connect(self.iterate)
        self.progress_bar = QProgressBar()
        time_spin.setValue(50)
        time_spin.setRange(0, 1000)
        time_layout.addWidget(QLabel("Sleep Time (ms)"))
        time_layout.addWidget(time_spin)
        button_layout.addLayout(time_layout)

        tests = {
            'plot y': test_plot_y,
            'plot xy': test_plot_xy,
            'plot parametric': test_plot_xy_parametric,
            'plot z': test_plot_z,
            'plot huge': test_plot_huge,
            'append y': test_append_y,
            'append xy': test_append_xy,
            'append z': test_append_z,
            'label': test_label,
        }
        fn_text_widget = QPlainTextEdit()
        fn_text_widget.setMinimumWidth(500)

        def make_set_iterator(iter):
            def set_iterator():
                fn_text_widget.setPlainText(inspect.getsource(iter))
                QApplication.instance().processEvents()
                self.iterator = iter()
                self.timer.start()
            return set_iterator

        for name, iter in list(tests.items()):
            button = QPushButton(name)
            button.clicked.connect(make_set_iterator(iter))
            button_layout.addWidget(button)

        layout.addLayout(button_layout)
        text_layout = QVBoxLayout()
        text_layout.addWidget(fn_text_widget)
        text_layout.addWidget(self.progress_bar)
        layout.addLayout(text_layout)

    def iterate(self):
        try:
            next(self.iterator)
            self.progress_bar.setValue(self.progress_bar.value() + 1)
        except StopIteration:
            self.timer.stop()
            self.progress_bar.setValue(0)

if __name__ == "__main__":
    app = QApplication([])
    c = LivePlotClient(size=2**28)
    win = TestWindow()
    win.show()
    def clean():
        c.close()
        sys.exit()
    signal.signal(signal.SIGINT, lambda sig, frame: clean())
    app.exec_()
    clean()
