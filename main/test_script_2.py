import time
from matplotlib import pyplot as plt
import numpy as np

x2 = np.array([1,2,3]);
y2 = np.array([1,2,3]);


def live_update_demo(x, y, blit = False):

    fig = plt.figure()
    ax2 = fig.add_subplot(1, 1, 1)
    line, = ax2.plot([], lw=3)

    fig.canvas.draw()   # note that the first draw comes before setting data 

    ax2.set_xlim(x.min(), x.max())
    ax2.set_ylim(y.min(), y.max())


    if blit:
        # cache the background
        ax2background = fig.canvas.copy_from_bbox(ax2.bbox)

    plt.show(block=False)

    line.set_data(x, y)

    if blit:
        # restore background
        fig.canvas.restore_region(ax2background)

            # redraw just the points
        ax2.draw_artist(line)

            # fill in the axes rectangle
        fig.canvas.blit(ax2.bbox)

            # in this post http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
            # it is mentionned that blit causes strong memory leakage. 
            # however, I did not observe that.

    else:
            # redraw everything
        fig.canvas.draw()

    fig.canvas.flush_events()
        #alternatively you could use
    plt.pause(2) 
        # however plt.pause calls canvas.draw(), as can be read here:
        #http://bastibe.de/2013-05-30-speeding-up-matplotlib.html


live_update_demo(x2,y2,True)   # 175 fps
#live_update_demo(False) # 28 fps