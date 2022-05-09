"""Finding lines"""
# Find Lines Example
#
# This example shows off how to find lines in the image. For each line object
# found in the image a line object is returned which includes the line's rotation.

# Note: Line detection is done by using the Hough Transform:
# http://en.wikipedia.org/wiki/Hough_transform
# Please read about it above for more information on what `theta` and `rho` are.

# find_lines() finds infinite length lines. Use find_line_segments() to find non-infinite lines.
import time

import sensor

# import image now is unused


ENABLE_LENS = False  # turn on for straighter lines...
thresholds_orange = [(34, 79, -5, 120, 0, 20)]  # для оранжевой линии

sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # grayscale is faster
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time=2000)
clock = time.clock()

# All line objects have a `theta()` method to get their rotation angle in degrees.
# You can filter lines based on their rotation angle.

MIN_DEGREE = 0
MAX_DEGREE = 179

# All lines also have `x1()`, `y1()`, `x2()`, and `y2()` methods to get their end-points
# and a `line()` method to get all the above as one 4 value tuple for `draw_line()`.


def catch_first_line_r(lines):
    """func is seeing for lines"""
    r_min_ind = 0
    r_min = 160 * 120

    for l_ind in lines:
        if l_ind.x1() * (120 - l_ind.y1()) < r_min:
            r_min = l_ind.x1() * (120 - l_ind.y1())
            r_min_ind = l_ind.index()
    return r_min_ind


while True:
    clock.tick()
    img = sensor.snapshot()
    if ENABLE_LENS:
        img.lens_corr(1.8)  # for 2.8mm lens...

    lines = []
    for l in img.find_line_segments(
        roi=(20, 60, 120, 30), merge_distance=40, max_theta_difference=25
    ):
        if (MIN_DEGREE <= l.theta()) and (l.theta() <= MAX_DEGREE):
            img.draw_line(l.line(), color=(255, 0, 0), thickness=5)
            # Добавление координат конечных точек прямой в общий массив
            lines.append(l)

    r_min_ind = catch_first_line_r(lines)
    if 0 <= r_min_ind < len(lines):
        img.draw_line(lines[r_min_ind].line(), color=(0, 255, 0), thickness=5)
        # Получение нужной линии
        impLine = lines[r_min_ind]
        # Определение нужного угла
        angle = 90 - impLine.theta()
        print(angle, "x1:", impLine.x1(), "y1:", impLine.y1())
        print("x2:", impLine.x2(), "y2:", impLine.y2())

        # blobs_in_line = img.find_blobs(thresholds_orange, roi=(impLine.x1(), impLine.y1(),
        # impLine.x1()-impLine.x2(), impLine.y1()-impLine.y2()),
        # pixels_threshold=200, area_threshold=200)
        # if len(blobs_in_line) != 0:
        # print("yes")

    # print("FPS %f" % clock.fps())

# About negative rho values:
#
# A [theta+0:-rho] tuple is the same as [theta+180:+rho].
# image.crop([x_scale=1.0[, y_scale=1.0[,
# roi=None[, rgb_channel=-1[, alpha=256[, color_palette=None[,
# alpha_palette=None[, hint=0[, x_size=None[, y_size=None[, copy=False]]]]]]]]]]])"""
