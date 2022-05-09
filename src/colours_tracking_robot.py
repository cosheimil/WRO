"""
Colours robot
sensor, image - working with Camera
time and math do logic in the code
"""
import math
import time

import sensor

# import image now is unused


# Color Tracking Thresholds (L Min, L Max, A Min, A Max, B Min, B Max)
# The below thresholds track in general red/green things. You may wish to tune them...
# thresholds = [(0, 100, 37, 127, 11, 127), # generic_red_thresholds #done
# (0, 73, -128, -18, 16, 127), # generic_green_thresholds #done
# (0, 15, 0, 40, -80, -20)] # generic_blue_thresholds

# thresholds для нужных цветов
threshold_red = [(0, 100, 37, 127, 11, 127)]
threshold_green = [(0, 73, -128, -18, 16, 127)]
thresholds = [threshold_red, threshold_green]

# You may pass up to 16 thresholds above. However, it's not really possible to segment any
# scene with 16 thresholds before color thresholds start to overlap heavily.

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking
clock = time.clock()

# Only blobs that with more pixels than "pixel_threshold" and more area than "area_threshold" are
# returned by "find_blobs" below. Change "pixels_threshold" and "area_threshold" if you change the
# camera resolution. Don't set "merge=True" becuase that will merge blobs which we don't want here.

dict_of_blobs_dimensions = {"red": 0, "green": 0}

while True:
    clock.tick()
    img = sensor.snapshot()
    # Цикл по 2 видам threshold
    for work_threshold in thresholds:
        for blob in img.find_blobs(
            work_threshold, pixels_threshold=200, area_threshold=200
        ):
            # These values depend on the blob not being circular - otherwise they will be shaky.
            if blob.elongation() > 0.5:
                img.draw_edges(blob.min_corners(), color=(255, 0, 0))
                img.draw_line(blob.major_axis_line(), color=(0, 255, 0))
                img.draw_line(blob.minor_axis_line(), color=(0, 0, 255))
            # These values are stable all the time.
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())
            # Note - the blob rotation is unique to 0-180 only.
            img.draw_keypoints(
                [(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20
            )
            # Получение размеров цилиндра на кадре
            blob_area = blob.area()
            if work_threshold == threshold_red:
                COLOR = "red"
            else:
                COLOR = "green"
            # Запись в нужное значение в словаре
            dict_of_blobs_dimensions[COLOR] = blob_area
    # Проверка, какой цилиднр ближе по площади
    if dict_of_blobs_dimensions["red"] == max(dict_of_blobs_dimensions.values()):
        print("right")
    else:
        print("left")
    # print(clock.fps())
