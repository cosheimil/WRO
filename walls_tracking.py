# Multi Color Blob Tracking Example
#
# This example shows off multi color blob tracking using the OpenMV Cam.

import sensor, image, time, math

# Color Tracking Thresholds (L Min, L Max, A Min, A Max, B Min, B Max)
# The below thresholds track in general red/green things. You may wish to tune them...
thresholds = [(0, 8, -128, 5, -17, 12)]
# You may pass up to 16 thresholds above. However, it's not really possible to segment any
# scene with 16 thresholds before color thresholds start to overlap heavily.

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False) # must be turned off for color tracking
sensor.set_auto_whitebal(False) # must be turned off for color tracking
clock = time.clock()



# Получение 2 самых больших блобов
def two_max_blobs(array):
    if len(array) >= 2:
        maxx = array[0]

        for i in array:
            if i.area() > maxx.area():
                maxx = i
        for i in array:
            if i != maxx:
                perMaxx = i
                break

        for i in array:
            if i.area() > perMaxx.area() and i != maxx:
                perMaxx = i

        return [maxx, perMaxx]


def catch_right_wall(walls):
    if walls[0].cx() < walls[1].cx():
        return walls[1]
    return walls[0]

def catch_left_wall(walls):
    if walls[0].cx() < walls[1].cx():
        return walls[0]
    return walls[1]

def detect_ways(walls):
    if (walls[0].cx() < walls[1].cx()):
        return walls
    return [walls[1], walls[0]]


# Only blobs that with more pixels than "pixel_threshold" and more area than "area_threshold" are
# returned by "find_blobs" below. Change "pixels_threshold" and "area_threshold" if you change the
# camera resolution. Don't set "merge=True" becuase that will merge blobs which we don't want here.

while(True):
    arrayOfBlobs = []
    clock.tick()
    img = sensor.snapshot()
    for blob in img.find_blobs(thresholds, roi=(0, 100, 320, 140), pixels_threshold=200, area_threshold=200):
        # These values depend on the blob not being circular - otherwise they will be shaky.
        # lastTest roi=(0, 160, 320, 80)
        if blob.elongation() > 0.5:
            img.draw_edges(blob.min_corners(), color=(255,0,0))
            img.draw_line(blob.major_axis_line(), color=(0,255,0))
            img.draw_line(blob.minor_axis_line(), color=(0,0,255))
        # These values are stable all the time.
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        # Note - the blob rotation is unique to 0-180 only.
        img.draw_keypoints([(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20)
        # Добавление определенного объекта
        arrayOfBlobs.append(blob)
    #for i in arrayOfBlobs:
     #   print(i.area(),end=" ")
    #print()
    # Делаем упрощение, что блобы в максимальные размерами - стены
    if len(arrayOfBlobs) >= 2:
        walls = two_max_blobs(arrayOfBlobs)
        #rightWall = catch_right_wall(walls)
        #leftWall = catch_left_wall(walls)
        walls = detect_ways(walls)
        print(walls[0].area() - walls[1].area())
    # Случае того, что он видит одну стенку очень близко, нужно вывыести ее
    # координату с целью понимая, левая она или правая и вывести area
    elif len(arrayOfBlobs) == 1:
        wall = arrayOfBlobs[0]
        # Если стенка слева, то поворот направо
        if (wall.cx() < 160):
            print(wall.area() / 2)

        else:

            print(-(wall.area() / 2))

    #print(clock.fps())
