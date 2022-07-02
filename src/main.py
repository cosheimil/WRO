import time
import math
import sensor
# import image now is unused
import pyb
import utime

# загружаем настройки


# ROI = Rectangle Of Interest (x, y, width, height)
# Левый и правый сектор определяют, в какой части изображания ищутся стенки
# Можешь менять, но они должны быть одинаковые по площади (width * height)
# Размеры полного изображения - 80 * 60 (width * height)
# LINESROI - для нахождения линий на полу (не зависит от LEFTROI и RIGHTROI)
LEFTROI = (0, 0, 60, 120)
RIGHTROI = (100, 0, 60, 120)
LINESROI = (0, 20, 160, 100)
CUBESROI = (0, 0, 160, 120)

LEFTROI_TEST = (0, 50, 40, 60)  # 120 * 160
RIGHTROI_TEST = (80, 50, 40, 60)

# Для определения цветов
# Если тут проблемы, то в OpenMV IDE Инструменты => Машинное зрение => Threshold Editor
# Там подбираешь так, чтобы объект нужного цвета был белый, кортеж копируешь сюда
thresholds = [(0, 19, -128, 127, -128, 127)]  # Черные стенки
# thresholds_blue_line = []  # Синий цвет
# 2 54 -6 52 -128 -5
thresholds_blue_line = [(2, 54, -6, 52, -128, -5)]
thresholds_orange_line = [(19, 58, 9, 64, 1, 76)]


thresholds_green_cube = [(15, 70, -83, -15, 13, 74)]  # цвет зеленого кубика
#thresholds_green_cube1 = [(18, 54, -66, -18, 13, 55)]
#thresholds_green_cube2 = [(17, 49, -79, -15, 14, 74)]
#thresholds_green_cube3 = [(26, 70, -79, -15, 14, 73)]
#thresholds_green_cube4 = [(15, 68, -83, -15, 14, 73)]

thresholds_red_cube = [(0, 53, 5, 70, 12, 54)]  # цвет красного кубика
#thresholds_red_cube1 = [(0, 53, 5, 63, 11, 41)]
#thresholds_red_cube2 = [(9, 43, 12, 69, -22, 54)]
#thresholds_red_cube3 = [(0, 46, 6, 68, 2, 42)]
#thresholds_red_cube4 = [(0, 53, 5, 63, -2, 37)]

thresholds_red_test = [(0, 24, 12, 68, -30, 81)]

MAX_SPEED = 50
MIN_SPEED = 100
CUBE_SPEED = 55

# Максимально маленькое delay
DELAY = 1  # Время торможения и ускорения в секундах

# Угол, при котором он едет прямо (под нашего настрой)
ZERO_ANGLE = 30

# Угол, на который он будет поворачивать направо/налево при виде линий
# Для нашего робота может быть что-то другое, но важно, что
# ZERO_ANGLE - RIGHT_ANGLE  = ZERO_ANGLE - LEFT_ANGLE
RIGHT_ANGLE = 0
LEFT_ANGLE = 60

# Максимальный (по модулю) угол отклонения колес от оси, при котороый
# он едет прямо (под нашего настрой)
MAX_ANGLE = 30

pix_thr = 50
area_thr = 50
CRIT_AREA = 450
NORMAL_WEIGHT = 400

DEBUG = 1

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)  # 80 * 60 / 160 * 120
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False, 3.52183)
sensor.set_auto_whitebal(False, rgb_gain_db=(61.4454, 60.2071, 64.5892))
sensor.set_auto_exposure(False, 10124)
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()

pinADir0 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1 = pyb.Pin('P3', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1.value(1)
tim = pyb.Timer(2, freq=1000)
chA = tim.channel(3, pyb.Timer.PWM, pin=pyb.Pin("P4"))
servo = pyb.Servo(1)
button = pyb.Pin('P1', pyb.Pin.IN, pyb.Pin.PULL_NONE)

servo.angle(ZERO_ANGLE)
chA.pulse_width_percent(MIN_SPEED)


def start_moving():
    # Плавный старт
    for c_speed in range(MIN_SPEED, MAX_SPEED, -10):
        chA.pulse_width_percent(c_speed)
        utime.sleep(DELAY / ((MAX_SPEED - MIN_SPEED) / 10))


def stop_moving():
    # Плавная остановка
    for c_speed in range(MAX_SPEED, MIN_SPEED, 10):
        chA.pulse_width_percent(c_speed)
        utime.sleep(DELAY / ((MAX_SPEED - MIN_SPEED) / 10))


def find_cube(roi, c_thresholds):
    # Поиск кубов нужного цвета в roi
    cubes = img.find_blobs(c_thresholds, roi=roi, pixels_threshold=pix_thr, area_threshold=area_thr)
    if len(cubes) != 0:
        big_cube = cubes[0]
        s = 0
        for c in cubes:
            s += c.pixels()
            if c.pixels() > big_cube.pixels():
                big_cube = c
        return big_cube, s
    else:
        return 0, 0


def find_blobs_weight(img, roi):
    """Для определения самого большого видимого блоба в этой части"""
    # Находятся все блобы в секторе и выбирается самый большой по площади
    # Возвращает кол-во черных пикселей и сам объект
    blobs = img.find_blobs(thresholds, roi=roi, pixels_threshold=250, area_threshold=250)  # 200 200
    s = 0
    for i in blobs:
        s += i.pixels()
        draw_blob(i, img)
    return s


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

# consts for work
FLAG = ""
LASTFLAG = ""
CORNER_COUNT = 0

# while button.value() == 0:
# pass

start_moving()

pid_red_cube = [0.25, 0.5, 0]  # 0.4 0.5 0
p_dx = 0
ROTATE = ''

t = pyb.millis()

while True:
    clock.tick()
    blue_lines = []
    orange_lines = []

    # Здесь проверка на кол-во пройденных поворотов
    if CORNER_COUNT == 12:
        t = pyb.millis()
    if CORNER_COUNT >= 12:
        # stop_moving()
        # chA.pulse_width_percent(100)
        if pyb.millis() - t > 1000:
            break

    img = sensor.snapshot().lens_corr(1.0, 1.0)

    # Поиск линий
    for blob in img.find_blobs(thresholds_blue_line, pixels_threshold=80, roi=LINESROI,
                               area_threshold=80):
        draw_blob(blob, img)
        # print(blob.rotation_deg())
        blue_lines.append(blob)

    for blob in img.find_blobs(thresholds_orange_line, pixels_threshold=80, roi=LINESROI,
                               area_threshold=80):
        #draw_blob(blob, img)
        orange_lines.append(blob)

    # Определение цвета найденной линии (если нашлась)
    if len(blue_lines) != 0 or len(orange_lines) != 0:
        if len(orange_lines) != 0:
            FLAG = "orange"
            if ROTATE == '':
                ROTATE = 'clockwise'
        elif len(orange_lines) == 0 and len(blue_lines) != 0:
            FLAG = "blue"
            if ROTATE == '':
                ROTATE = 'counter_clockwise'

    green_cube, green_cube_weight = find_cube(CUBESROI, thresholds_green_cube)
    red_cube, red_cube_weight = find_cube(CUBESROI, thresholds_red_cube)


    # На время квалов

    if red_cube:
        print(red_cube.cx())
        print('red:', red_cube.pixels())
    if green_cube:
        print('green:', green_cube.pixels())
        print(green_cube.cx())
    if red_cube_weight != 0 and red_cube.cx() > 30 and red_cube.pixels() >= CRIT_AREA:
        print('yes red:', red_cube.cx())
        print('yes red:', red_cube.pixels())
        #debug
        draw_blob(red_cube, img)
        #debug
        cube_x = red_cube.cx()
        if red_cube.pixels() >= CRIT_AREA:
            dx = CUBESROI[2] - cube_x
            angle = ZERO_ANGLE - (pid_red_cube[0] * dx + pid_red_cube[1] * (dx - p_dx))
            if angle > LEFT_ANGLE:
                angle = LEFT_ANGLE
            elif angle < RIGHT_ANGLE:
                angle = RIGHT_ANGLE
            servo.angle(angle)
        chA.pulse_width_percent(CUBE_SPEED)

    elif green_cube_weight != 0 and green_cube.cx() < 130 and green_cube.pixels() >= CRIT_AREA:
        print('yes green:', green_cube.cx())
        print('yes green:', green_cube.pixels())

        # debug
        draw_blob(green_cube, img)
        # debug
        if green_cube.pixels() >= CRIT_AREA:
            cube_x = green_cube.cx()
            dx = CUBESROI[2] - cube_x
            angle = ZERO_ANGLE + (pid_red_cube[0] * dx + pid_red_cube[1] * (dx - p_dx))
            if angle > LEFT_ANGLE:
                angle = LEFT_ANGLE
            elif angle < RIGHT_ANGLE:
                angle = RIGHT_ANGLE
            servo.angle(angle)
            chA.pulse_width_percent(CUBE_SPEED)

    elif len(img.find_blobs(thresholds, pixels_threshold=250, area_threshold=250)) != 0:
        print('внутри определения')
        left_blob_weight = find_blobs_weight(img, LEFTROI)
        right_blob_weight = find_blobs_weight(img, RIGHTROI)
        if ROTATE == '':

            print('right_blob_weight', right_blob_weight)
            print('left_blob_weight', left_blob_weight)

            dif = left_blob_weight - right_blob_weight
            print(dif)
            dif_percent = dif / (LEFTROI[2] * LEFTROI[3]) * 3
            dif_percent = max(dif_percent, -1)
            dif_percent = min(dif_percent, 1)
            servo.angle(-dif_percent * MAX_ANGLE + ZERO_ANGLE)
            chA.pulse_width_percent(MAX_SPEED)
        elif ROTATE == 'clockwise':

            if right_blob_weight >= 2300:
                left_blob_weight -= 550
            # Поменять на / 400 на финале (?)
            servo.angle(-MAX_ANGLE * (left_blob_weight - 880) / 1100 + ZERO_ANGLE)

            print("left_blob_weight:", left_blob_weight)

            chA.pulse_width_percent(MAX_SPEED)

        elif ROTATE == 'counter_clockwise':
            if left_blob_weight >= 2300:
                right_blob_weight -= 550

            # Поменять на /400 на финале (?)
            servo.angle(MAX_ANGLE * (right_blob_weight - 880) / 1100 + ZERO_ANGLE)

            print("right_blob_weight:", right_blob_weight)

            chA.pulse_width_percent(MAX_SPEED)
    else:
        chA.pulse_width_percent(MAX_SPEED)

    # Подсчет кол-ва пройденных поворотов (прохождение каждой линии - половина поворота)
    if LASTFLAG != FLAG:
        LASTFLAG = FLAG
        CORNER_COUNT += 0.5

    if green_cube_weight == 0 and red_cube_weight == 0:
        p_dx = 0

    # img.binary(thresholds_red_cube)
    # img.erode(2)
    # img.dilate(2)
    # img.binary(thresholds_red_test)
stop_moving()
