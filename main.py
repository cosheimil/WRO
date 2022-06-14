"""Multi Color Blob Tracking Example"""
import time
import math
import sensor
# import image now is unused
import pyb
import time
# загружаем настройки


# ROI = Rectangle Of Interest (x, y, width, height)
# Левый и правый сектор определяют, в какой части изображания ищутся стенки
# Можешь менять, но они должны быть одинаковые по площади (width * height)
# Размеры полного изображения - 80 * 60 (width * height)
# LINESROI - для нахождения линий на полу (не зависит от LEFTROI и RIGHTROI)
LEFTROI = (0, 0, 40, 60)
RIGHTROI = (40, 0, 40, 60)
LINESROI = (0, 35, 80, 25)
CUBESROI = (0, 0, 80, 60)


# Для определения цветов
# Если тут проблемы, то в OpenMV IDE Инструменты => Машинное зрение => Threshold Editor
# Там подбираешь так, чтобы объект нужного цвета был белый, кортеж копируешь сюда
thresholds = [(0, 17, -14, 12, -8, 22)]  # Черные стенки
# thresholds_blue_line = []  # Синий цвет
thresholds_blue_line = [(24, 54, -36, 11, -44, -5)]# мои, на месте
thresholds_orange_line = [(25, 47, 6, 68, -2, 57)]  # Оранжевый цвет
thresholds_green_cube = [(30, 100, -74, -15, 29, 83)] # цвет зеленого кубика
thresholds_red_cube = [(19, 79, 24, 127, -15, 127)] # цвет красного кубика


# Хз почему, но тут вроде инвертировано, но проверь на тренировочной заезде
# Если при MIN_SPEED = 100 не тормозит, то ставь 0
MAX_SPEED = 40
MIN_SPEED = 100
# Максимально маленькое delay
DELAY = 1 # Время торможения и ускорения в секундах

# Угол, при котором он едет прямо (под нашего настрой)
ZERO_ANGLE = -45

# Угол, на который он будет поворачивать направо/налево при виде линий
# Для нашего робота может быть что-то другое, но важно, что
# ZERO_ANGLE - RIGHT_ANGLE  = ZERO_ANGLE - LEFT_ANGLE
# RIGHT_ANGLE = -80
# LEFT_ANGLE = -10

# Максимальный (по модулю) угол отклонения колес от оси, при котороый
# он едет прямо (под нашего настрой)
MAX_ANGLE = 36


DEBUG = 1


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQQVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()



pinADir0 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1 = pyb.Pin('P5', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1.value(1)
tim = pyb.Timer(2, freq=1000)
chA = tim.channel(3, pyb.Timer.PWM, pin=pyb.Pin("P4"))
servo = pyb.Servo(2)
button = pyb.Pin("P0", pyb.Pin.PULL_NONE ,pyb.Pin.IN)

servo.angle(ZERO_ANGLE)
chA.pulse_width_percent(MIN_SPEED)


def start_moving():
    # Плавный старт
    for c_speed in range(MIN_SPEED, MAX_SPEED, 10):
        chA.pulse_width_percent(c_speed)
        utime.sleep(DELAY / ((MAX_SPEED - MIN_SPEED) / 10))


def stop_moving():
    # Плавная остановка
    for c_speed in range(MAX_SPEED, MIN_SPEED, -10):
        chA.pulse_width_percent(c_speed)
        utime.sleep(DELAY / ((MAX_SPEED - MIN_SPEED) / 10))


def find_cube(roi, c_thresholds):
    # Поиск кубов нужного цвета в roi
    cube = img.find_blobs(c_thresholds, roi=roi, pixels_threshold=200, area_threshold=200)
    if len(cube) != 0:
        return cube.area()
    else:
        return 0


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
CORNER_COUNT = 0


while button.value() == 0:
    pass

start_moving()

while True:
    clock.tick()
    blue_lines = []
    orange_lines = []
    # Здесь проверка на кол-во пройденных поворотов
    if CORNER_COUNT < 12:
        chA.pulse_width_percent(MAX_SPEED)
    else:
        servo.angle(ZERO_ANGLE)
        break


    # Получение изображения с камеры
    img = sensor.snapshot().lens_corr(1.9, 1.2)

    # Поиск линий
    for blob in img.find_blobs(thresholds_blue_line, pixels_threshold=200, roi=LINESROI,
                               area_threshold=200):
        draw_blob(blob, img)
        # print(blob.rotation_deg())
        blue_lines.append(blob)

    for blob in img.find_blobs(thresholds_orange_line, pixels_threshold=200, roi=LINESROI,
                               area_threshold=200):
        draw_blob(blob, img)
        orange_lines.append(blob)

    # Определение цвета найденной линии (если нашлась)
    if len(blue_lines) != 0 or len(orange_lines) != 0:

        if len(orange_lines) != 0:
            FLAG = "orange"
        elif len(orange_lines) == 0 and len(blue_lines) != 0:
            FLAG = "blue"

        ROTATION = True

    else:
        ROTATION = False

    temp_deg = 0
    # Действия в том случае, если перед нами поворот
    if ROTATION:
        if FLAG == "blue":
            if blue_lines[len(blue_lines)-1].rotation_deg() > 90:
                temp_deg = blue_lines[len(blue_lines)-1].rotation_deg() - 180
            else:
                temp_deg = blue_lines[len(blue_lines)-1].rotation_deg()
        else:
            if orange_lines[len(orange_lines)-1].rotation_deg() > 90:
                temp_deg = orange_lines[len(orange_lines)-1].rotation_deg() - 180
            else:
                temp_deg = orange_lines[len(orange_lines)-1].rotation_deg()
        if ZERO_ANGLE - temp_deg * 4 < RIGHT_ANGLE:
            servo.angle(RIGHT_ANGLE)
        elif ZERO_ANGLE - temp_deg * 4 > LEFT_ANGLE:
            servo.angle(LEFT_ANGLE)
        else:
            servo.angle(ZERO_ANGLE - int(temp_deg * 4))





    elif len(img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200)) != 0:

        # Здесь определяется площадь черных стенок справа и слева
        left_blob_weight, left_blob = find_biggest_blob(img, LEFTROI)
        right_blob_weight, right_blob = find_biggest_blob(img, RIGHTROI)

        # Поиск зеленого и красного куба
        green_cube_weight = find_cube(CUBESROI, thresholds_green_cube)
        red_cube_weight = find_cube(CUBESROI, thresholds_red_cube)

        # Добавление поправки из-за кубов
        left_blob_weight += red_cube_weight
        right_blob_weight += green_cube_weight

        # Отрисовка (при дебаге)
        draw_blob(left_blob, img)
        draw_blob(right_blob, img)

        # На основе разницы кол-ва черного справа и слева поворачиваем на угол
        dif = left_blob_weight - right_blob_weight
        
        # Почекать коэф (4) - возможно ее не должно быть
        dif_percent = int(dif / (LEFTROI[2] * LEFTROI[3]) * 4)

        servo.angle(-dif_percent * MAX_ANGLE + ZERO_ANGLE)

    # Подсчет кол-ва пройденных поворотов (прохождение каждой линии - половина поворота)
    if LASTFLAG != FLAG:
        LASTFLAG = FLAG
        CORNER_COUNT += 0.5
        
stop_moving()
"""
while True:
    pass
"""
"""
pinADir1 = pyb.Pin('P5', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1.value(1)
"""
"""
past = pyb.millis()
while pyb.millis() - past < 5000:
    pass
"""

pinADir0 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1.value(0)
pinADir0.value(0)
