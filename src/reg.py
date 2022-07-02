"""Multi Color Blob T[racking Example"""
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
CUBESROI = (0, 30, 160, 90)

LEFTROI_TEST = (0, 50, 40, 60) # 120 * 160
RIGHTROI_TEST = (80, 50, 40, 60)

# Для определения цветов
# Если тут проблемы, то в OpenMV IDE Инструменты => Машинное зрение => Threshold Editor
# Там подбираешь так, чтобы объект нужного цвета был белый, кортеж копируешь сюда
thresholds = [(0, 19, -128, 127, -128, 127)]  # Черные стенки
# thresholds_blue_line = []  # Синий цвет
thresholds_blue_line = [(12, 40, -1, 43, -75, -24)]
thresholds_orange_line = [(19, 42, 9, 51, 7, 70)]
# (19, 42, 9, 51, 7, 70)

thresholds_green_cube = [(24, 46, -56, -10, 10, 51)] # цвет зеленого кубика
thresholds_red_cube = [(6, 42, 6, 63, -28, 47)] # цвет красного кубика

thresholds_red_test = [(0, 24, 12, 68, -30, 81)]


MAX_SPEED = 50
MIN_SPEED = 100
CUBE_SPEED = 55


# Максимально маленькое delay
DELAY = 1 # Время торможения и ускорения в секундах

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

pix_thr = 130
area_thr = 130
CRIT_AREA = 145
NORMAL_WEIGHT = 400

DEBUG = 1


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA) # 80 * 60 / 160 * 120
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False, 4.21671)
sensor.set_auto_whitebal(False, rgb_gain_db=(61.3194, 60.2071, 64.7213))
#sensor.set_auto_exposure(False, 101244)
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()


pinADir0 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1 = pyb.Pin('P3', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
pinADir1.value(1)
tim = pyb.Timer(2, freq=1000)
chA = tim.channel(3, pyb.Timer.PWM, pin=pyb.Pin("P4"))
servo = pyb.Servo(1)
button = pyb.Pin('P1', pyb.Pin.IN, pyb.Pin.PULL_UP)

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
        for c in cubes:
            if c.pixels() > big_cube.pixels():
                big_cube = c
        return big_cube, big_cube.pixels()
    else:
        return 0, 0


def find_blobs_weight(img, roi):
    """Для определения самого большого видимого блоба в этой части"""
    # Находятся все блобы в секторе и выбирается самый большой по площади
    # Возвращает кол-во черных пикселей и сам объект
    blobs = img.find_blobs(thresholds, roi=roi, pixels_threshold=250, area_threshold=250)# 200 200
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

while True:
    clock.tick()
    print(button.value())


utime.sleep(2)

start_moving()


pid_red_cube = [0.25, 0.7, 0] # 0.4 0.5 0
p_dx = 0
ROTATE = ''


chA.pulse_width_percent(MAX_SPEED)
utime.sleep(5)
stop_moving()


