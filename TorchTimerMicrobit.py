# Sets all the Halo LEDs to orange, and then darkens one each second,
# going clockwise from the top, and displays an image in the center.
# Note: The time calculations all rely on setting the real-time clock
# back to zero every time we reset. Because we're expecting the minutes
# and seconds to start at zero every time.

# from microbit import *
from microbit import button_a
from microbit import button_b
from microbit import display
from microbit import Image
from microbit import i2c
from microbit import accelerometer
# from microbit import pin0 #mic input
from microbit import pin8  # ZIP LEDs
# from microbit import pin14 #buzzer
from microbit import pin19  # I2C
from microbit import pin20  # I2C
from neopixel import NeoPixel
import gc


global clock
global halo_leds


# Some constants
NUM_LEDS_ON_HALO = 60
LED_BLACK = (0, 0, 0)
ICON_PLAY = Image("09000:09900:09990:09900:09000")
ICON_PAUSED = Image("99099:99099:99099:99099:99099")
ICON_FINISHED = Image("90009:09090:00900:09090:90009")

# Flame temperature in degrees centigrade
T1300 = (30, 20,  0)  # brightest yellow
T1200 = (25, 15,  0)
T1100 = (20, 10,  0)
T1000 = (15,  5,  0)  # red-orange
T0250 = (5,  5, 15)  # blue/indigo

# Notes: 50 is too bright, and too much red looks quite unlike a flame.
torchImage60x1 = [T1300, T1300, T1300, T1300, T1300,
                  T1300, T1300, T1300, T1300, T1300,
                  T1200, T1200, T1200, T1200, T1200,
                  T1100, T1100, T1100, T1100, T1100,
                  T1100, T1100, T1100, T1100, T1100,
                  T1000, T1000, T1000, T1000, T0250,
                  T0250, T0250, T1000, T1000, T1000,
                  T1100, T1100, T1100, T1100, T1100,
                  T1100, T1100, T1100, T1100, T1100,
                  T1200, T1200, T1200, T1200, T1200,
                  T1300, T1300, T1300, T1300, T1300,
                  T1300, T1300, T1300, T1300, T1300]

class KitronikRTC:
    CHIP_ADDRESS = 0x6F
    RTC_SECONDS_REG = 0x00
    RTC_MINUTES_REG = 0x01
    RTC_HOURS_REG = 0x02
    RTC_WEEKDAY_REG = 0x03
    RTC_DAY_REG = 0x04
    RTC_MONTH_REG = 0x05
    RTC_YEAR_REG = 0x06
    RTC_CONTROL_REG = 0x07
    RTC_OSCILLATOR_REG = 0x08
    RTC_PWR_UP_MINUTE_REG = 0x1C
    START_RTC = 0x80
    STOP_RTC = 0x00
    ENABLE_BATTERY_BACKUP = 0x08
    seconds = 0
    minutes = 0
    hours = 0
    paused = False
    readCurrentSeconds = 0

    def __init__(self):
        i2c.init(freq=100000, sda=pin20, scl=pin19)
        writeBuf = bytearray(2)
        readBuf = bytearray(1)
        readWeekDayReg = 0
        writeBuf[0] = self.RTC_SECONDS_REG
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        readBuf = i2c.read(self.CHIP_ADDRESS, 1, False)
        readCurrentSeconds = readBuf[0]
        writeBuf[0] = self.RTC_CONTROL_REG
        writeBuf[1] = 0x43
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_WEEKDAY_REG
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        readBuf = i2c.read(self.CHIP_ADDRESS, 1, False)
        readWeekDayReg = readBuf[0]
        writeBuf[0] = self.RTC_WEEKDAY_REG
        writeBuf[1] = self.ENABLE_BATTERY_BACKUP | readWeekDayReg
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = self.START_RTC | readCurrentSeconds
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)

    # reads the RTC chip. Result comes back as BCD, so this function
    # converts them as they come in and places them into the class members
    def readValue(self):
        writeBuf = bytearray(1)
        readBuf = bytearray(7)
        self.readCurrentSeconds = 0
        writeBuf[0] = self.RTC_SECONDS_REG
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        readBuf = i2c.read(self.CHIP_ADDRESS, 7, False)
        self.seconds = (((readBuf[0] & 0x70) >> 4) * 10) + (readBuf[0] & 0x0F)
        self.minutes = (((readBuf[1] & 0x70) >> 4) * 10) + (readBuf[1] & 0x0F)
        self.hours = (((readBuf[2] & 0x30) >> 4) * 10) + (readBuf[2] & 0x0F)
        self.weekDay = readBuf[3]
        self.day = (((readBuf[4] & 0x30) >> 4) * 10) + (readBuf[4] & 0x0F)
        self.month = (((readBuf[5] & 0x10) >> 4) * 10) + (readBuf[5] & 0x0F)
        self.year = (((readBuf[6] & 0xF0) >> 4) * 10) + (readBuf[6] & 0x0F)

    # This actually pokes the time values into the RTC chip.
    # It converts the decimal values to BCD for the RTC chip
    def setTime(self, newHours, newMinutes, newSeconds):
        writeBuf = bytearray(2)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = self.STOP_RTC
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_HOURS_REG
        writeBuf[1] = (int(newHours / 10) << 4) | int(newHours % 10)
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_MINUTES_REG
        writeBuf[1] = (int(newMinutes / 10) << 4) | int(newMinutes % 10)
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = (
            self.START_RTC | (int(newSeconds / 10) << 4) | int(newSeconds % 10)
        )
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        self.paused = False

    # Must account for this exceeding 59 minutes or, in the
    # case that minuteDelta is -ve, below 0 minutes.
    def addMinutes(self, minuteDelta):
        self.readValue()
        newMinutes = self.minutes + minuteDelta
        newHours = self.hours
        if newMinutes > 59:
            newMinutes = newMinutes - 60
            newHours += 1
        elif newMinutes < 0:
            newMinutes = 0
            newHours = 0
        clock.setTime(newHours, newMinutes, self.seconds)

    def hourHasElapsed(self):
        if self.hours > 0:
            return True

    def pause(self):
        if self.paused:
            return
        writeBuf = bytearray(2)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = self.STOP_RTC
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        self.paused = True

    def unpause(self):
        if not self.paused:
            return
        writeBuf = bytearray(2)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = self.START_RTC | self.seconds
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        self.paused = False

# ==================== End of class KitronikRTC ====================
gc.collect()  # Presumably cleans up after all the writeBuf reassignments

def lightLEDs(fromLED, toLED):
    # some guardrails:
    if fromLED > 59:
        fromLED = 59
    if toLED > 60:
        toLED = 60
    if fromLED < 0:
        fromLED = 0
    if toLED < -1:
        toLED = -1
    # are we counting up or down?
    step = 1
    if toLED < fromLED:
        step = -1
    # Python ranges don't include the final value (toLED)
    for i in range(fromLED, toLED, step):
        halo_leds[i] = torchImage60x1[i]
    halo_leds.show()

def resetLEDs():
    lightLEDs(0, 60)

def extinguishLEDs(toLED):
    for i in range(0, toLED):
        halo_leds[i] = LED_BLACK
    halo_leds.show()

def resetTorch():
    clock.setTime(0, 0, 0)  # This also unpauses it
    resetLEDs()
    gc.collect()


# Initialise the Halo HD, which is basically a neopixel strip with 60 LEDs,
# plus a clock and a few other things.
halo_leds = NeoPixel(pin8, NUM_LEDS_ON_HALO)
clock = KitronikRTC()
resetTorch()


while True:
    if accelerometer.was_gesture("shake"):
        # Reset the timer and LEDs, and unpause.
        resetTorch()

    if accelerometer.was_gesture("face down"):
        clock.pause()

    if accelerometer.was_gesture("face up"):
        clock.unpause()

    clock.readValue()

    if button_a.was_pressed():
        clock.addMinutes(10)

    if button_b.was_pressed():
        previousMinutes = clock.minutes
        clock.addMinutes(-10)
        clock.readValue()
        lightLEDs(previousMinutes, clock.minutes-1)

    numExtinguishable = clock.minutes
    if clock.hourHasElapsed():
        numExtinguishable = 60
    extinguishLEDs(numExtinguishable)

    if clock.hourHasElapsed():
        display.show(ICON_FINISHED)
    elif clock.paused:
        display.show(ICON_PAUSED)
    else:
        display.show(ICON_PLAY)
