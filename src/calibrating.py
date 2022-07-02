"""Multi Color Blob Tracking Example"""
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
LEFTROI = (0, 20, 80, 100)
RIGHTROI = (80, 0, 80, 120)
LINESROI = (0, 20, 160, 100)
CUBESROI = (0, 0, 160, 120)

LEFTROI_TEST = (0, 0, 65, 120)

# Для определения цветов
# Если тут проблемы, то в OpenMV IDE Инструменты => Машинное зрение => Threshold Editor
# Там подбираешь так, чтобы объект нужного цвета был белый, кортеж копируешь сюда
thresholds = [(0, 17, -14, 12, -8, 22)]  # Черные стенки
# thresholds_blue_line = []  # Синий цвет
thresholds_blue_line = [(24, 54, -36, 11, -44, -5)]# мои, на месте
thresholds_orange_line = [(0, 100, 7, 41, -3, 61)]  # Оранжевый цвет
thresholds_green_cube = [(30, 100, -74, -15, 29, 83)] # цвет зеленого кубика
thresholds_red_cube = [(26, 35, 26, 59, -7, 36)] # цвет красного кубика
thresholds_red_test = [(0, 40, 13, 68, -30, 81)]

# Хз почему, но тут вроде инвертировано, но проверь на тренировочной заезде
# Если при MIN_SPEED = 100 не тормозит, то ставь 0
MAX_SPEED = 35
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

pix_thr = 10
area_thr = 10
CRIT_AREA = 150
NORMAL_WEIGHT = 1000

DEBUG = 1


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA) # 80 * 60 / 160 * 120
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False)
sensor.set_vflip(True)
sensor.set_hmirror(True)
clock = time.clock()


f = open('cal.txt', 'a')
print('gain:', sensor.get_gain_db(),'\n')
print('exposure:', sensor.get_exposure_us(),'\n')
print('whitebal:', sensor.get_rgb_gain_db(),'\n')
#f.write('gain:', sensor.get_gain_db(),'\n')
#f.write('exposure:', sensor.get_exposure_us(),'\n')
#f.write('whitebal:', sensor.get_rgb_gain_db(),'\n')
f.close()

while True:
    clock.tick()
    img = sensor.snapshot().lens_corr(1.0, 1.0) # 1.9, 1.2

