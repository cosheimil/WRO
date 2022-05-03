"""Multi Color Blob Tracking Example"""
#
# This example shows off multi color blob tracking using the OpenMV Cam.
import time
import math
import sensor
# import image now is unused
import pyb

# Color Tracking Thresholds (L Min, L Max, A Min, A Max, B Min, B Max)
# The below thresholds track in general red/green things. You may wish to tune them...
thresholds = [(0, 12, -128, 8, -10, 47)] #black walls
thresholds_blue_line = [(19, 100, -1, 20, -128, -15)] # синий цвет
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


def find_blob(img, roi):
    """Определения размера рандомного блоба из списка блобов в этой части"""
    for blob in img.find_blobs(thresholds, roi=roi, pixels_threshold=200, area_threshold=200):
        density = blob.density()
        return density * blob.area(), blob
        #return blob
    return False, False


def find_biggest_blob(img, roi):
    """Для определения самого большого видимого блоба в этой части"""
    blobs = img.find_blobs(thresholds, roi=roi, pixels_threshold=200, area_threshold=200)
    if len(blobs) == 0:
        return False, False

    max_blob = blobs[0]
    for blob in blobs:
        if blob.area() > max_blob.area():
            max_blob = blob
    return max_blob.density() * max_blob.area(), max_blob



def draw_blob(blob, img):
    """drawing blobs"""
    if blob:
        if blob.elongation() > 0.5:
            img.draw_edges(blob.min_corners(), color=(255,0,0))
            img.draw_line(blob.major_axis_line(), color=(0,255,0))
            img.draw_line(blob.minor_axis_line(), color=(0,0,255))
        img.draw_rectangle(blob.rect())
        img.draw_cross(blob.cx(), blob.cy())
        img.draw_keypoints([(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20)

def sum_weights(lines):
    summary_weight = 0
    for l in lines:
        summary_weight += l.area()
    return summary_weight

ERR = 0
OLDDIF = 0
MAX_ERROR = 10000
MIN_ERROR = -10000
KP = 1.5
KD = 0.5
KI = 0.5


def pid(dif):
    """Описание ПИД регулятора для системы"""
    global ERR, OLDDIF

    proportional = dif * KP
    defferential = (dif - OLDDIF)* KD

    ERR += dif
    ERR = max(ERR, MIN_ERROR)
    ERR = min(ERR, MAX_ERROR)

    # if ERR < MIN_ERROR:
    #     ERR = MIN_ERROR
    # if ERR > MAX_ERROR:
    #     ERR = MAX_ERROR
    integral = ERR * KI

    OLDDIF = dif
    return (proportional + defferential + integral) / 20400

LEFTROI = (0, 160, 120, 80)
RIGHTROI = (200, 160, 120, 80)
ROTATION = False
FLAG = ""
LASTFLAG = ""
NOTCHECKED = True
ROTK = 0

while True:
    clock.tick()
    chA.pulse_width_percent(60)

    blue_lines = []
    orange_lines = []
    # Убираем "рыбий глаз"

    img = sensor.snapshot().lens_corr(strength = 3, zoom = 1.2)

    for blob in img.find_blobs(thresholds_blue_line, pixels_threshold=200, roi=(0, 160, 320, 80),
                               area_threshold=200):
        draw_blob(blob, img)
        blue_lines.append(blob)

    for blob in img.find_blobs(thresholds_orange_line, pixels_threshold=200, roi=(0, 160, 320, 80),
                               area_threshold=200):
        draw_blob(blob, img)
        orange_lines.append(blob)

    if len(blue_lines) != 0 or len(orange_lines) != 0:
        # блок для определения направления
        if NOTCHECKED:
            if len(orange_lines) != 0:
                FLAG = "orange"
            else:
                FLAG = "blue"
            NOTCHECKED = False
        # блок определения последней линии, чтобы понимать направление дальше
        # пусть если видит линию, то меняет показателей в зависимости от цвета
        # поворот направо - отрицательное значение
        if len(orange_lines) != 0:
            ROTK -= sum_weights(orange_lines)
        elif len(orange_lines) == 0 and len(blue_lines) != 0:
            ROTK += sum_weights(blue_lines)
        ROTATION = True

    else:
        ROTATION = False

    if ROTATION:
        print("ROTATION true")

        #if FLAG == "blue":
            #print("right")
            #servo.angle(20)
        #else:
            #print("left")
            #servo.angle(-10)
        if ROTK / 100 < 0:
            print("right")
            servo.angle(-10)
            #servo.angle((ROTK * 36 + 6) % 30)
        else:
            print("left")
            servo.angle(20)
            #servo.angle((ROTK * 36 + 6) % 30)
    else:
        print("ROTATION false")
        if len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)) != 0:

            # Идея: искать блобы в левой и правой половине катинки
            # Найти черные блобы в правой и левой части
            # Сравнить кол-во пикселей справа и слева
            # Определить, куда двигаться
            leftBlobWeight, leftBlob = find_biggest_blob(img, LEFTROI)
            rightBlobWeight, rightBlob = find_biggest_blob(img, RIGHTROI)
            draw_blob(leftBlob, img)
            draw_blob(rightBlob, img)

            dif = leftBlobWeight - rightBlobWeight

            #difPersent = pid(dif)
            difPersent = dif / 9600

            print(-difPersent * 36 + 6)

            servo.angle((-difPersent * 36 + 6))
            #chA.pulse_width_percent(20)


        # Делаем определение в правой и левой части, чтобы
        # там найти блобы и понять их размеры
