# Multi Color Blob Tracking Example
#
# This example shows off multi color blob tracking using the OpenMV Cam.

import sensor, image, time, math, pyb

# Color Tracking Thresholds (L Min, L Max, A Min, A Max, B Min, B Max)
# The below thresholds track in general red/green things. You may wish to tune them...
thresholds = [(0, 12, -128, 8, -10, 47)] #black walls
thresholds_blue_line = [(0, 100, 12, 120, -56, -6)] # синий цвет
thresholds_orange_line = [((0, 100, 3, 120, -4, 127))] # оранж цвет
# You may pass up to 16 thresholds above. However, it's not really possible to segment any
# scene with 16 thresholds before color thresholds start to overlap heavily.

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False) # must be turned off for color tracking
sensor.set_auto_whitebal(False) # must be turned off for color tracking
clock = time.clock()

pinADir0 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1 = pyb.Pin('P5', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)

pinADir1.value(1)

tim = pyb.Timer(2, freq=1000)

chA = tim.channel(3, pyb.Timer.PWM, pin=pyb.Pin("P4"))

servo = pyb.Servo(2)

# Определения размера рандомного блоба из списка блобов в этой части
def find_blob(img, ROI):
    for blob in img.find_blobs(thresholds, roi=ROI, pixels_threshold=200, area_threshold=200):
        density = blob.density()
        return density * blob.area(), blob
        #return blob
    return False, False

# Для определения самого большого видимого блоба в этой части
def find_biggest_blob(img, ROI):
    blobs = img.find_blobs(thresholds, roi=ROI, pixels_threshold=200, area_threshold=200)
    if len(blobs) == 0:
        return False, False

    maxBlob = blobs[0]
    for blob in blobs:
        if blob.area() > maxBlob.area():
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


err = 0
oldDif = 0
MAX_ERROR = 10000
MIN_ERROR = -10000
KP = 1.5
KD = 0.5
KI = 0.5

# Описание ПИД регулятора для системы
def PID(dif):
    global err, oldDif;

    proportional = dif * KP
    defferential = (dif - oldDif)* KD

    err += dif
    if err < MIN_ERROR:
        err = MIN_ERROR
    if err > MAX_ERROR:
        err = MAX_ERROR
    integral = err * KI

    oldDif = dif
    return (proportional + defferential + integral) / 20400

LeftROI = (0, 160, 160, 80)
RightROI = (160, 160, 160, 80)
rotation = False
flag = ""
lastflag = ""
non_checked = True

while(True):
    clock.tick()
    blue_lines = []
    orange_lines = []
    # Убираем "рыбий глаз"

    img = sensor.snapshot().lens_corr(strength = 3, zoom = 1.2)

    for blob in img.find_blobs(thresholds_blue_line, pixels_threshold=200, roi=(0, 120, 320, 120), area_threshold=200):
        draw_blob(blob, img)
        blue_lines.append(blob)

    for blob in img.find_blobs(thresholds_orange_line, pixels_threshold=200, roi=(0, 120, 320, 120), area_threshold=200):
        draw_blob(blob, img)
        orange_lines.append(blob)

    if len(blue_lines) != 0 or len(orange_lines) != 0:
        # блок для определения направления
        if non_checked:
            if len(orange_lines) != 0:
                flag = "orange"
            else:
                flag = "blue"
            checked = False
        #
        # блок определения последней линии, чтобы понимать направление дальше
        if len(orange_lines) != 0:
            lastflag = "orange"
        elif len(orange_lines) == 0 and len(blue_lines) != 0:
            lastflag = "blue"
        rotation = True
    else:
        flag = lastflag
        rotation = False

    if rotation:
        print("rotation true")

        if flag == "blue":
            print("right")
            servo.angle(20)
        else:
            print("left")
            servo.angle(-10)
    else:
        print("rotation false")
        if len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)) != 0:

            # Идея: искать блобы в левой и правой половине катинки
            # Найти черные блобы в правой и левой части
            # Сравнить кол-во пикселей справа и слева
            # Определить, куда двигаться
            leftBlobWeight, leftBlob = find_biggest_blob(img, LeftROI)
            rightBlobWeight, rightBlob = find_biggest_blob(img, RightROI)
            draw_blob(leftBlob, img)
            draw_blob(rightBlob, img)

            dif = leftBlobWeight - rightBlobWeight

            #difPersent = PID(dif)
            difPersent = dif / 20400

            print(-difPersent * 36 + 6)

            servo.angle((-difPersent * 36 + 6) % 30)
            chA.pulse_width_percent(50)


        # Делаем определение в правой и левой части, чтобы
        # там найти блобы и понять их размеры








