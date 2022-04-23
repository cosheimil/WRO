import sensor, image, time, math


enable_lens_corr = False
thresholds = [(0, 12, -128, 8, -10, 47)]

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False) # must be turned off for color tracking
sensor.set_auto_whitebal(False) # must be turned off for color tracking
clock = time.clock()

# Определения размера рандомного блоба из списка блобов в этой части
def find_blob(img, ROI):
    for blob in img.find_blobs(thresholds, roi=ROI, pixels_threshold=200, area_threshold=200):
        density = blob.density()
        return density * blob.area(), blob
    return False, False

# Для определения самого большого видимого блоба в этой части
def find_biggest_blob(img, ROI):
    blobs = img.find_blobs(thresholds, roi=ROI, pixels_threshold=200, area_threshold=200)
    if len(blobs) == 0:
        return False, False

    maxBlob = blobs[0]
    for blob in blobs:
        if blob.density() > maxBlob.density():
            maxBlob = blob
    return maxBlob.density() * maxBlob.area(), maxBlob



def draw_blob(blob, img):
    if blob:
        if blob.elongation() > 0.5:
            img.draw_edges(blob.min_corners(), color=(255,0,0))
            img.draw_line(blob.major_axis_line(), color=(0,255,0))
            img.draw_line(blob.minor_axis_line(), color=(0,0,255))
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        img.draw_keypoints([(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20)

def catch_first_line_r(lines):
    rMinInd = 0
    rMin = 160 * 120

    for lInd in range(len(lines)):
        if lines[lInd].x1() * (120 - lines[lInd].y1()) < rMin:
            rMin = lines[lInd].x1() * (120 - lines[lInd].y1())
            rMinInd = lInd
    return rMinInd


LeftROI = (0, 160, 160, 80)
RightROI = (160, 160, 160, 80)
min_degree = 0
max_degree = 179


while(True):
    clock.tick()
    img = sensor.snapshot()

    ############# lines #############
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
        print(angle)

    ######################################





    # Делаем определение в правой и левой части, чтобы
    # там найти блобы и понять их размеры

    print(len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)))
    if len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)) != 0:

        leftBlobWeight, leftBlob = find_biggest_blob(img, LeftROI)
        rightBlobWeight, rightBlob = find_biggest_blob(img, RightROI)
        draw_blob(leftBlob, img)
        draw_blob(rightBlob, img)

        if (leftBlobWeight > rightBlobWeight):
            print("right")
        else:
            print("left")

