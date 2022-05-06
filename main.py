"""Multi Color Blob Tracking Example"""
import time
import math
import sensor
# import image now is unused
import pyb

# загружаем настройки
from settings import *


DEBUG = False


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()

pinADir0 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1 = pyb.Pin('P5', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1.value(1)
tim = pyb.Timer(2, freq=1000)
chA = tim.channel(3, pyb.Timer.PWM, pin=pyb.Pin("P4"))
servo = pyb.Servo(2)


def find_biggest_blob(img, roi):
    """Для определения самого большого видимого блоба в этой части"""
    # Находятся все блобы в секторе и выбирается самый большой по площади
    # Возвращает кол-во черных пикселей и сам объект
    blobs = img.find_blobs(thresholds, roi=roi, pixels_threshold=200, area_threshold=200)
    if len(blobs) == 0:
        return False, False
    max_blob = blobs[0]
    for blob in blobs:
        if blob.area() > max_blob.area():
            max_blob = blob
    return max_blob.density() * max_blob.area(), max_blob


if DEBUG:
    def draw_blob(blob, img):
        """drawing blobs"""
        if blob:
            if blob.elongation() > 0.5:
                img.draw_edges(blob.min_corners(), color=(255, 0, 0))
                img.draw_line(blob.major_axis_line(), color=(0, 255, 0))
                img.draw_line(blob.minor_axis_line(), color=(0, 0, 255))
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())
            img.draw_keypoints([(blob.cx(), blob.cy(), int(math.degrees(blob.rotation())))], size=20)

else:
    def draw_blob(blob, img):
        pass


# Считает суммарную площадь объектов
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


# ПИД-регулятор
def pid(dif):
    """Описание ПИД регулятора для системы"""
    global ERR, OLDDIF

    proportional = dif * KP
    defferential = (dif - OLDDIF) * KD

    ERR += dif
    ERR = max(ERR, MIN_ERROR)
    ERR = min(ERR, MAX_ERROR)
    integral = ERR * KI

    OLDDIF = dif
    return (proportional + defferential + integral)


# consts for work
ROTATION = False
FLAG = ""
LASTFLAG = ""
NOTCHECKED = True
ROTK = 0
CORNER_COUNT = 0

while True:
    clock.tick()
    blue_lines = []
    orange_lines = []

    # Здесь проверка на кол-во пройденных поворотов
    if CORNER_COUNT <= 12:
        chA.pulse_width_percent(MAX_SPEED)
    else:
        chA.pulse_width_percent(MIN_SPEED)

    # Получение изображения с камеры
    img = sensor.snapshot()

    # Поиск линий
    for blob in img.find_blobs(thresholds_blue_line, pixels_threshold=200, roi=LINESROI,
                               area_threshold=200):
        draw_blob(blob, img)
        blue_lines.append(blob)

    for blob in img.find_blobs(thresholds_orange_line, pixels_threshold=200, roi=LINESROI,
                               area_threshold=200):
        draw_blob(blob, img)
        orange_lines.append(blob)

    # Определение цвета найденной линии (если нашлась)
    if len(blue_lines) != 0 or len(orange_lines) != 0:

        # ROTK - коэффициент, определяющий направление поворота
        # ROTK < 0 => поворот направо, иначе налево
        if len(orange_lines) != 0:
            ROTK -= sum_weights(orange_lines)
            FLAG = "orange"
        elif len(orange_lines) == 0 and len(blue_lines) != 0:
            ROTK += sum_weights(blue_lines)
            FLAG = "blue"

        ROTATION = True

    else:
        ROTATION = False

    # Действия в том случае, если перед нами поворот
    if ROTATION:

        if ROTK / 100 < 0:
            servo.angle(RIGHT_ANGLE)
        else:
            servo.angle(LEFT_ANGLE)

    elif len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)) != 0:

        # Здесь определяется площадь черных стенок справа и слева
        left_blob_weight, left_blob = find_biggest_blob(img, LEFTROI)
        right_blob_weight, right_blob = find_biggest_blob(img, RIGHTROI)

        # Отрисовка (при дебаге)
        draw_blob(left_blob, img)
        draw_blob(right_blob, img)

        # На основе разницы кол-ва черного справа и слева поворачиваем на угол
        dif = left_blob_weight - right_blob_weight
        dif_percent = dif / (LEFTROI[3] * LEFTROI[4])

        servo.angle(-dif_percent * MAX_ANGLE + ZERO_ANGLE)

    # Подсчет кол-ва пройденных поворотов (прохождение каждой линии - половина поворота)
    if LASTFLAG != FLAG:
        LASTFLAG = FLAG
        CORNER_COUNT += 0.5
