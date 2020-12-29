import numpy as np
import matplotlib.pyplot as plt


class plot_1d():

    def initialize_1d(self):
        #Set up plot
        self.figure, self.ax = plt.subplots(facecolor=(24/256, 25/256, 26/256))
        self.lines, = self.ax.plot([],[], color='#ffac00')
        self.ax.set_facecolor((24/256, 25/256, 26/256))
        self.ax.tick_params(labelcolor=(255/256, 172/256, 0))
        self.figure.canvas.draw() 
        self.figure.show()
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True) # check, probably useless
        self.ax.set_autoscalex_on(True)
        #Other stuff
        #self.ax.grid()

    def update_1d(self, xdata, ydata, blit = True):
        
        if blit:
        # cache the background
            axbackground = self.figure.canvas.copy_from_bbox(self.ax.bbox)

        #plt.show(block=False)

        self.lines.set_data(xdata, ydata)
        self.ax.set_xlim(0, 50)
        self.ax.set_ylim(-1, 10)
        #self.ax.relim()
        #self.ax.autoscale_view()
        #self.ax.set_autoscaley_on(True)

        if blit:
        # restore background
            self.figure.canvas.restore_region(axbackground)
            self.ax.draw_artist(self.lines)
            self.figure.canvas.blit(self.ax.bbox)
        else:
            # redraw everything
            self.figure.canvas.draw()

        self.figure.canvas.draw_idle()
        self.figure.canvas.start_event_loop(0.001)
        #self.figure.canvas.flush_events()

    def finish_1d(self):
        self.figure.show()
        # there is a problem with keeping the graph window open...
