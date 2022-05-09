"""Testing all funcs 2gether"""
import math
import time

import sensor

# import image now is unused


ENABLE_LENS_COR = False
thresholds = [(0, 12, -128, 8, -10, 47)]

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking
clock = time.clock()


def find_blob(img, roi):
    """Определения размера рандомного блоба из списка блобов в этой части"""
    for blob in img.find_blobs(
        thresholds, roi=roi, pixels_threshold=200, area_threshold=200
    ):
        density = blob.density()
        return density * blob.area(), blob
    return False, False


def find_biggest_blob(img, roi):
    """Для определения самого большого видимого блоба в этой части"""
    blobs = img.find_blobs(
        thresholds, roi=roi, pixels_threshold=200, area_threshold=200
    )
    if len(blobs) == 0:
        return False, False

    max_blob = blobs[0]
    for blob in blobs:
        if blob.density() > max_blob.density():
            max_blob = blob
    return max_blob.density() * max_blob.area(), max_blob


def draw_blob(blob, img):
    """now we r drawing this blob"""
    if blob:
        if blob.elongation() > 0.5:
            img.draw_edges(blob.min_corners(), color=(255, 0, 0))
            img.draw_line(blob.major_axis_line(), color=(0, 255, 0))
            img.draw_line(blob.minor_axis_line(), color=(0, 0, 255))
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        img.draw_keypoints(
            [(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20
        )


def catch_first_line_r(lines):
    """func is seeing for lines"""
    r_min_ind = 0
    r_min = 160 * 120

    for l_ind in lines:
        if l_ind.x1() * (120 - l_ind.y1()) < r_min:
            r_min = l_ind.x1() * (120 - l_ind.y1())
            r_min_ind = l_ind.index()
    return r_min_ind


Leftroi = (0, 160, 160, 80)
Rightroi = (160, 160, 160, 80)
MIN_GEGREE = 0
MAX_DEGREE = 179


while True:
    clock.tick()
    img = sensor.snapshot()

    ############# lines #############
    if ENABLE_LENS_COR:
        img.lens_corr(1.8)  # for 2.8mm lens...

    lines = []
    for l in img.find_line_segments(
        roi=(20, 60, 120, 30), merge_distance=40, max_theta_difference=25
    ):
        if (MIN_GEGREE <= l.theta()) and (l.theta() <= MAX_DEGREE):
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
        print(angle)

    ######################################

    # Делаем определение в правой и левой части, чтобы
    # там найти блобы и понять их размеры

    print(len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)))
    if len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)) != 0:

        leftBlobWeight, leftBlob = find_biggest_blob(img, Leftroi)
        rightBlobWeight, rightBlob = find_biggest_blob(img, Rightroi)
        draw_blob(leftBlob, img)
        draw_blob(rightBlob, img)

        if leftBlobWeight > rightBlobWeight:
            print("right")
        else:
            print("left")
