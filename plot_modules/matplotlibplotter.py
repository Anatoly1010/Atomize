import matplotlib.pyplot as plt
import numpy as np

class plot_1d():

    def initialize_1d(self):
        #Set up plot
        self.figure, self.ax = plt.subplots()
        self.lines, = self.ax.plot([],[])
        self.figure.canvas.draw() 
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True) # check, probably useless
        self.ax.set_autoscalex_on(True)
        #Other stuff
        #self.ax.grid()

    def update_1d(self, xdata, ydata, blit = False):
        
        if blit:
        # cache the background
            ax2background = self.figure.canvas.copy_from_bbox(self.ax.bbox)

        plt.show(block=False)

        self.lines.set_data(xdata, ydata)
        self.ax.relim()
        self.ax.autoscale_view()

        if blit:
        # restore background
            self.figure.canvas.restore_region(ax2background)
            self.ax2.draw_artist(self.lines)
            self.figure.canvas.blit(self.ax.bbox)
        else:
            # redraw everything
            self.figure.canvas.draw()

        self.figure.canvas.flush_events()

    def finish_1d(self):
        plt.show()
        # there is a problem with keeping the graph window open...
