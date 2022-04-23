# Find Lines Example
#
# This example shows off how to find lines in the image. For each line object
# found in the image a line object is returned which includes the line's rotation.

# Note: Line detection is done by using the Hough Transform:
# http://en.wikipedia.org/wiki/Hough_transform
# Please read about it above for more information on what `theta` and `rho` are.

# find_lines() finds infinite length lines. Use find_line_segments() to find non-infinite lines.

enable_lens_corr = False # turn on for straighter lines...
thresholds_orange = [(34, 79, -5, 120, 0, 20)] # для оранжевой линии


import sensor, image, time

sensor.reset()
sensor.set_pixformat(sensor.RGB565) # grayscale is faster
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time = 2000)
clock = time.clock()

# All line objects have a `theta()` method to get their rotation angle in degrees.
# You can filter lines based on their rotation angle.

min_degree = 0
max_degree = 179

# All lines also have `x1()`, `y1()`, `x2()`, and `y2()` methods to get their end-points
# and a `line()` method to get all the above as one 4 value tuple for `draw_line()`.

def catch_first_line_r(lines):
    rMinInd = 0
    rMin = 160 * 120

    for lInd in range(len(lines)):
        if lines[lInd].x1() * (120 - lines[lInd].y1()) < rMin:
            rMin = lines[lInd].x1() * (120 - lines[lInd].y1())
            rMinInd = lInd
    return rMinInd

while(True):
    clock.tick()
    img = sensor.snapshot()
    if enable_lens_corr: img.lens_corr(1.8) # for 2.8mm lens...

    lines = []
    for l in img.find_line_segments(roi=(20, 60, 120, 30), merge_distance=40, max_theta_difference=25):
        if (min_degree <= l.theta()) and (l.theta() <= max_degree):
            img.draw_line(l.line(), color = (255, 0, 0), thickness=5)
            # Добавление координат конечных точек прямой в общий массив
            lines.append(l)

    rMinInd = catch_first_line_r(lines)
    if (rMinInd < len(lines) and rMinInd >= 0):
        img.draw_line(lines[rMinInd].line(), color=(0, 255, 0), thickness=5)
    # Получение нужной линии
        impLine = lines[rMinInd]
    # Определение нужного угла
        angle = 90 - impLine.theta()
        print(angle, "x1:", impLine.x1(), "y1:", impLine.y1())
        print("x2:", impLine.x2(), "y2:", impLine.y2())

        #blobs_in_line = img.find_blobs(thresholds_orange, roi=(impLine.x1(), impLine.y1(), impLine.x1()-impLine.x2(), impLine.y1()-impLine.y2()), pixels_threshold=200, area_threshold=200)
        #if len(blobs_in_line) != 0:
            #print("yes")


    #print("FPS %f" % clock.fps())

# About negative rho values:
#
# A [theta+0:-rho] tuple is the same as [theta+180:+rho].
#image.crop([x_scale=1.0[, y_scale=1.0[, roi=None[, rgb_channel=-1[, alpha=256[, color_palette=None[, alpha_palette=None[, hint=0[, x_size=None[, y_size=None[, copy=False]]]]]]]]]]])
