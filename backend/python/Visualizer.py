import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from backend.python.location.Location import Location

from backend.python.enums import Mobility, Shape, State
from backend.python.transport import Bus, Walk

point_colors = {State.SUSCEPTIBLE.value: 'b', State.INFECTED.value: 'r', State.RECOVERED.value: 'g'}
point_edgecolors = {Bus.__name__.split('.')[-1]: [0, 1, 1, 0.1], Walk.__name__.split('.')[-1]: [1, 0, 1, 0.1]}

point_names = {State.SUSCEPTIBLE.value: State.SUSCEPTIBLE.name,
               State.INFECTED.value: State.INFECTED.name,
               State.RECOVERED.value: State.RECOVERED.name}
test_center_color = 'yellow'


def add_to_line(ax, line_no, data, delta=False):
    x, y = ax.lines[line_no].get_data()
    if delta:
        data = y[-1] + data
    x, y = np.append(x, len(x)), np.append(y, data)
    ax.lines[line_no].set_xdata(x), ax.lines[line_no].set_ydata(y)
    return y


def plot_info(fig, axs, points):
    temps = [p.temp for p in points]
    state = [p.state for p in points]

    df = pd.DataFrame({"Temp": temps, "State": state})

    axs[0, 0].cla()
    sns.histplot(df, x="Temp", hue="State", ax=axs[0, 0])

    ax = axs[0, 1]
    s, i, r = sum(df["State"] == State.SUSCEPTIBLE.value), sum(df["State"] == State.INFECTED.value), sum(
        df["State"] == State.RECOVERED.value)
    if len(ax.lines) == 0:
        ax.plot([s])
        ax.plot([i])
        ax.plot([r])
        ax.legend(["S", "I", "R"])
        y_s = s
        y_i = i
        y_r = r

    else:
        max_value = 0

        y = add_to_line(ax, 0, s)
        y_s = y[-2]
        max_value = max(max_value, max(y))

        y = add_to_line(ax, 1, i)
        y_i = y[-2]
        max_value = max(max_value, max(y))

        y = add_to_line(ax, 2, r)
        y_r = y[-2]
        max_value = max(max_value, max(y))

        ax.set_xlim(0, len(y))
        ax.set_ylim(0, max_value + 2)
        fig.canvas.draw(), fig.canvas.flush_events()

    ax = axs[1, 0]
    cum_positive = np.array([p.tested_positive_time for p in points])
    cum_positive = sum(cum_positive >= 0)
    cum_r = r
    if len(ax.lines) == 0:
        daily_positive = cum_positive
        daily_new = i
        daily_r = r
        ax.plot([cum_positive])
        ax.plot([i])
        ax.plot([cum_r])
        ax.legend(["Cumulative tested positive", "Cumulative true positive", "Cumulative recovered"])

    else:
        max_value = 0
        y = add_to_line(ax, 0, cum_positive)
        daily_positive = y[-1] - y[-2]
        daily_r = r - y_r
        max_value = max(max_value, max(y))

        daily_new = i - y_i + daily_r
        y = add_to_line(ax, 1, daily_new, delta=True)
        max_value = max(max_value, max(y))

        y = add_to_line(ax, 2, daily_r, delta=True)
        max_value = max(max_value, max(y))

        ax.set_xlim(0, len(y))
        ax.set_ylim(0, max_value + 2)
        fig.canvas.draw(), fig.canvas.flush_events()

    ax = axs[1, 1]
    if len(ax.lines) == 0:
        ax.plot([daily_positive])
        ax.plot([daily_new])
        ax.plot([daily_r])
        ax.legend(["Daily tested positive", "Daily true positive", "Daily recovered"])
    else:
        max_value = 0
        y = add_to_line(ax, 0, daily_positive)
        max_value = max(max_value, max(y))

        y = add_to_line(ax, 1, daily_new)
        max_value = max(max_value, max(y))

        y = add_to_line(ax, 2, daily_r)
        max_value = max(max_value, max(y))

        ax.set_xlim(0, len(y))
        ax.set_ylim(0, max_value + 2)
        fig.canvas.draw(), fig.canvas.flush_events()


def get_heatmap(points, h, w):
    res = 20
    yy, xx = np.meshgrid(np.linspace(-h, h, res), np.linspace(-w, w, res))
    zz = np.zeros_like(xx)
    dw, dh = (2 * w + 1) / res, (2 * h + 1) / res
    for p in points:
        if p.state == State.INFECTED.value:
            zz[int(p.x // dw) + res // 2, int(p.y // dh) + res // 2] += 1
    return xx, yy, zz


def init_figure(root, points, test_centers, h, w):
    fig = plt.figure(1)
    ax = plt.gca()

    # drawing heat-map
    xx, yy, zz = get_heatmap(points, h, w)
    hm = ax.pcolormesh(xx, yy, zz, cmap='Reds', shading='auto', alpha=0.9)
    fig.colorbar(hm, ax=ax)

    # drawing points
    x, y = [p.x for p in points], [p.y for p in points]
    if len(points) > 10000:
        x, y = [], []
    sc = plt.scatter(x, y, alpha=0.8)
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=point_names[key], markerfacecolor=point_colors[key],
               markersize=15) for key in point_colors.keys()
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    # drawing test centers
    test_center_patches = []
    for test in test_centers:
        circle = plt.Circle((test.x, test.y), test.r, color=test_center_color, fill=True, alpha=0.3)
        ax.add_patch(circle)
        test_center_patches.append(circle)

    # drawing locations
    def dfs(rr: Location):
        if rr.shape == Shape.CIRCLE.value:
            circle = plt.Circle((rr.x, rr.y), rr.radius, color='g', fill=False)
            ax.add_patch(circle)
        elif rr.shape == Shape.POLYGON.value:
            coord = rr.boundary
            coord = np.concatenate([coord, coord[0:1, :]], axis=0)  # repeat the first point to create a 'closed loop'
            xs, ys = coord[:, 0], coord[:, 1]  # create lists of x and y values
            ax.plot(xs, ys)
        x = rr.exit[0]
        y = rr.exit[1]
        ax.scatter(x, y, marker='x')
        ax.annotate(rr.name, (x, y), xytext=(x + 20, y + 20),
                    arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=-90"))
        for child in rr.locations:
            dfs(child)

    dfs(root)

    plt.xlim(-w, w)
    plt.ylim(-h, h)
    plt.draw()
    return fig, ax, sc, hm, test_center_patches


def update_figure(fig, ax, sc, hm, points, test_centers, test_center_patches, h, w):
    if len(points) <= 10000:
        x, y = [p.x for p in points], [p.y for p in points]

        sc.set_facecolor([point_colors[p.state] for p in points])
        sc.set_edgecolor([point_edgecolors[p.current_trans.__class__.__name__] for p in points])
        sc.set_linewidth([0.5 for _ in points])
        # s = np.array([p.state for p in points])
        # s = (s * 256 / 3)
        # sc.set_facecolor(plt.get_cmap('brg')(s))

        sc._sizes = [10 for _ in points]  # v
        sc.set_offsets(np.c_[x, y])

    # v = [(p.vx ** 2 + p.vy ** 2) ** 0.5 + 1 for p in points]

    for i, test in enumerate(test_centers):
        if i == len(test_center_patches):
            circle = plt.Circle((test.x, test.y), test.r, color=test_center_color, fill=True, alpha=0.3)
            ax.add_patch(circle)
            test_center_patches.append(circle)
        else:
            test_center_patches[i].center = test.x, test.y

    xx, yy, zz = get_heatmap(points, h, w)
    hm.set_array(zz.ravel())

    cbar = hm.colorbar
    vmax = max(cbar.vmax, np.max(zz))
    hm.set_clim(0, vmax)
    cbar_ticks = np.linspace(0., vmax, num=10, endpoint=True)
    cbar.set_ticks(cbar_ticks)
    cbar.draw_all()

    fig.canvas.draw_idle()
    plt.pause(0.01)
