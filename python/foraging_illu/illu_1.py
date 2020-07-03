# Author: Xiangwen Wang
# Illustration of information foraging on search engine

from pylab import *
from math import sin, cos, pi, tan
from matplotlib.axis import *
from matplotlib.font_manager import FontProperties

lattice_len = 12
site_size = 1
time = [0.0, 2.75, 2.5, 3.5]
lattice_shift_angle = 7 * pi / 18.0
position = [0.0, 0.0]
click_series = [2, 5, 11, 4]
linewidth = 3
font0 = FontProperties()
time_ellipsis = 2.75
dotcount = 9
arrowwidth = 20
radius = [0.55, 0.35, 0.32]
pagesize = 10


def addpage_bgcolor(x, y, lattice_len=lattice_len, site_size=site_size,
                    color=['#CCFFFF', '#FFFFCC'], linewidth=linewidth, pagesize=pagesize):
    x0, y0 = x, y
    x1 = x + pagesize * site_size
    broken_barh([(x0, pagesize * site_size), (x1, (lattice_len - pagesize + 1) * site_size)],
                (y0, site_size), facecolor=color, edgecolor='none')


def addlattice(x, y, lattice_len=lattice_len, site_size=site_size, color='k', linewidth=linewidth):
    x0, y0 = x, y
    xt, yt = x + (lattice_len + 1) * site_size, y + site_size
    plot([x0, xt], [y0, y0], '-', color=color, linewidth=linewidth)
    plot([x0, xt], [yt, yt], '-', color=color, linewidth=linewidth)
    for i in range(lattice_len + 1):
        plot([x0 + i * site_size, x0 + i * site_size], [y0, yt],
             '-', color=color, linewidth=linewidth)


def addbglines(lattice_origin, times, bg, lattice_len=lattice_len, site_size=site_size, color='#dddddd', linewidth=linewidth / 1.25):
    if bg:
        plot([lattice_origin[0][0], lattice_origin[-1][0]], [lattice_origin[0][1] + 1,
                                                             lattice_origin[-1][1] + 1], '-', color=color, linewidth=linewidth)
        plot([lattice_origin[0][0] + lattice_len * site_size, lattice_origin[-1][0] + lattice_len * site_size],
             [lattice_origin[0][1] + 1, lattice_origin[-1][1] + 1], '-', color=color, linewidth=linewidth)
    else:
        for i in range(len(time) - 1):
            plot([lattice_origin[i][0] + site_size / tan(lattice_shift_angle), lattice_origin[i + 1][0]],
                 [lattice_origin[i][1] + 1, lattice_origin[i + 1][1]], '-', color=color, linewidth=linewidth)
            plot([lattice_origin[i][0] + (1.0 / tan(lattice_shift_angle) + lattice_len) * site_size, lattice_origin[i + 1][0] +
                  lattice_len * site_size], [lattice_origin[i][1] + 1, lattice_origin[i + 1][1]], '-', color=color, linewidth=linewidth)


def addclickorder(lattice_origin, site_size=site_size, color='purple'):
    for i in range(len(lattice_origin) - 1):
        font = font0.copy()
        font.set_style('italic')
        text(lattice_origin[i][0] - site_size * 2.25, lattice_origin[i][1] + site_size / 5.0,
             'n=%d' % (i + 1), fontproperties=font, color=color, fontsize=26 * site_size, fontweight='medium')


def addtime(lattice_origin, lattice_len=lattice_len, site_size=site_size, color='purple'):
    for i in range(len(lattice_origin) - 1):
        font = font0.copy()
        font.set_style('italic')
        if i == 0:
            time_str = r't$_' + str(i + 1) + r'$=$0$'
        else:
            time_str = r't$_' + str(i + 1) + '$'
        text(lattice_origin[i][0] + (lattice_len + 1.35) * site_size, lattice_origin[i][1] + site_size / 5.0,
             time_str, fontproperties=font, color=color, fontsize=30 * site_size, fontweight='medium')


def addrank(xy, lattice_len=lattice_len, site_size=site_size, color='Brown'):
    x, y = xy[0], xy[1] - site_size * 0.55
    text(x - site_size * 0.75, y, 'r=', color=color,
         fontsize=20 * site_size, fontweight='semibold')
    fontsize = 16
    for i in range(lattice_len + 1):
        rank_char = str(i + 1)
        if i == lattice_len:
            rank_char = '...'
            dist = 0.2
            y = y + site_size * 0.15
            fontsize = 20
        elif i >= 9:
            dist = 0.2
        else:
            dist = 0.3
        text(x + site_size * (i + dist), y, rank_char, color=color,
             fontsize=fontsize * site_size, fontweight='semibold')


def adddotlines_epplipsis(lattice_origin, click_series, time_ellipsis, site_size=site_size, color='Orange',
                          linewidth=linewidth, ellipsis_color='#333333', ellipsis_size=linewidth * 2):
    lattice_with_ellipsis = lattice_origin
    lattice_with_ellipsis.append([lattice_origin[-1][0] + time_ellipsis * cos(
        lattice_shift_angle), lattice_origin[-1][1] + time_ellipsis * sin(lattice_shift_angle)])
    for i in range(len(click_series)):
        startposi = [lattice_with_ellipsis[i][
            0] + (click_series[i] - 0.5) * site_size, lattice_with_ellipsis[i][1] + site_size]
        endposi = [lattice_with_ellipsis[
            i + 1][0] + (click_series[i] - 0.5) * site_size, lattice_with_ellipsis[i + 1][1]]
        plot([startposi[0], endposi[0]], [startposi[1], endposi[1]],
             '--', color=color, linewidth=linewidth)
    ellipsis_position = [[endposi[0] - site_size * 0.75, endposi[0],
                          endposi[0] + site_size * 0.75], [endposi[1] + 0.1 * site_size] * 3]
    plot(ellipsis_position[0], ellipsis_position[
         1], u'o', markersize=ellipsis_size, color=ellipsis_color, mec=ellipsis_color)


def addstay(lattice_origin, click_series, site_size=site_size, color=['b', '#FF6666'], linewidth=linewidth * 1.65):
    for i in range(len(click_series)):
        preposi = [lattice_origin[i][
            0] + (click_series[i] - 0.5) * site_size, lattice_origin[i][1] + 0.5 * site_size]
        plot(preposi[0], preposi[1], marker=u'o', mec=color[
             0], markersize=17 * site_size, mew=linewidth, markerfacecolor='none')
        if i > 0.5:
            latposi = [lattice_origin[i][
                0] + (click_series[i - 1] - 0.5) * site_size, lattice_origin[i][1] + 0.5 * site_size]
            plot(latposi[0], latposi[1], marker=u'o', mec=color[
                1], markersize=17 * site_size, mew=linewidth, markerfacecolor='none')


def addjump(lattice_origin, click_series, site_size=site_size, color='Brown', arrowsize=arrowwidth, radius=radius):
    for i in range(1, len(lattice_origin) - 1):
        xy_ori = (lattice_origin[
            i - 1][0] + (click_series[i - 1] + 0.5) * site_size, lattice_origin[i][1] + site_size * (1 + 0.05))
        xy_tar = (lattice_origin[i][
            0] + (click_series[i] - 0.5) * site_size, lattice_origin[i][1] + site_size * (1 + 0.05))
        if xy_tar[0] < xy_ori[0]:
            sign = ''
        else:
            sign = '-'
        annotate('', xytext=xy_ori, xy=xy_tar, size=arrowsize,
                 arrowprops=dict(arrowstyle='simple', fc=color, ec=color, connectionstyle='arc3,rad=' + sign + str(radius[i - 1])),)


def addsteplength(lattice_origin, click_series, color='purple', boundary_color='#666666', linewidth=linewidth, site_size=site_size, arrowsize=arrowwidth / 2.0):
    font = font0.copy()
    font.set_style('italic')
    linesize = 0.75
    for i in range(1, len(lattice_origin) - 1):
        xy_tar = (lattice_origin[
            i - 1][0] + (click_series[i - 1] + 0.5) * site_size, lattice_origin[i][1] - site_size * (0.1))
        xy_ori = (lattice_origin[i][
            0] + (click_series[i] - 0.5) * site_size, lattice_origin[i][1] - site_size * (0.1))
        plot([xy_ori[0], xy_ori[0]], [
             xy_ori[1], xy_ori[1] - site_size * linesize], '-', color=boundary_color, linewidth=linewidth)
        plot([xy_tar[0], xy_tar[0]], [
             xy_tar[1], xy_tar[1] - site_size * linesize], '-', color=boundary_color, linewidth=linewidth)
        xy_mid = [(xy_tar[0] + xy_ori[0]) / 2.0,
                  (xy_tar[1] + xy_ori[1]) / 2.0 - linesize * site_size / 2.0]
        annotate('', xytext=[xy_mid[0] - 0.5 * site_size, xy_mid[1]], xy=[min(xy_tar[0], xy_ori[0]), xy_mid[1]], size=arrowsize,
                 arrowprops=dict(arrowstyle='simple', fc=color, ec=color),)
        annotate('', xytext=[xy_mid[0] + 0.5 * site_size, xy_mid[1]], xy=[max(xy_tar[0], xy_ori[0]), xy_mid[1]], size=arrowsize,
                 arrowprops=dict(arrowstyle='simple', fc=color, ec=color),)
        text(xy_mid[0] - 0.48 * site_size, xy_mid[1] - (1 - linesize + 0.1) * site_size, r'd$_' +
             str(i) + '$', fontproperties=font, color=color, fontsize=30 * site_size, fontweight='medium')


def main():
    lattice_origin = [position]
    for i in range(len(time)):
        lattice_origin.append([lattice_origin[i][0] + time[i] * cos(
            lattice_shift_angle), lattice_origin[i][1] + time[i] * sin(lattice_shift_angle)])
    lattice_origin = lattice_origin[1:]
    for i in range(len(time)):
        addpage_bgcolor(lattice_origin[i][0], lattice_origin[i][1])
    addbglines(lattice_origin, time, bg=True)
    addbglines(lattice_origin, time, bg=False)
    adddotlines_epplipsis(lattice_origin, click_series, time_ellipsis)
    for i in range(len(time)):
        addlattice(lattice_origin[i][0], lattice_origin[i][1])
    addclickorder(lattice_origin)  # add clicking order to the left side
    addtime(lattice_origin)  # add time to the right side
    addrank(lattice_origin[0])  # add rank at the bottom of the figure
    addstay(lattice_origin, click_series)  # mark the stay
    # add corresponding jump arrow in each step
    addjump(lattice_origin, click_series)
    # add d and two arrows besides it
    addsteplength(lattice_origin, click_series)
    # adjust figures
    subplots_adjust(
        left=0.03, bottom=0.03, right=0.97, top=0.97, wspace=0, hspace=0)
    axis([lattice_origin[0][0] - site_size * 2, lattice_origin[-1][0] + (lattice_len + 1) * site_size,
          lattice_origin[0][0] - site_size * 1, lattice_origin[-1][1] + site_size * 0.5])
    axis('off')
    savefig('illu_1.eps')
    savefig('illu_1.png')
    draw()
    # show()

if __name__ == '__main__':
    main()
