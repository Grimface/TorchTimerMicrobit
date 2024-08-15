# Sets all the Halo LEDs to orange, and then darkens one each second,
# going clockwise from the top, and displays an image in the center.
# Note: The time calculations all rely on setting the real-time clock
# back to zero every time we reset. Because we're expecting the minutes
# and seconds to start at zero every time.

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
from microbit import *

# Some constants
NUM_LEDS_ON_HALO = 60
LED_BLACK = (0, 0, 0)
ICON_PLAY = Image("09000:09900:09990:09900:09000")
ICON_PAUSED = Image("99099:99099:99099:99099:99099")

# Flame temperature in degrees centigrade
T1300 = (30, 20,  0) # brightest yellow
T1200 = (25, 15,  0)
T1100 = (20, 10,  0)
T1000 = (15,  5,  0) # red-orange
T0250 = ( 5,  5, 15) # blue/indigo

#Notes: 50 is too bright, and too much red looks quite unlike a flame.
torchImage60x1 = [T1300, T1300, T1300, T1300, T1300,
                  T1300, T1300, T1300, T1300, T1300,
                  T1200, T1200, T1200, T1200, T1200,
                  T1100, T1100, T1100, T1100, T1100,
                  T1100, T1100, T1100, T1100, T1100,
                  T1000, T1000, T1000, T1000, T0250,
                  T0250, T1000, T1000, T1000, T1000,
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
    currentMinutes = 0
    currentMinutes = 0
    currentHours = 0

    def __init__(self):
        i2c.init(freq=100000, sda=pin20, scl=pin19)
        writeBuf = bytearray(2)
        readBuf = bytearray(1)
        readCurrentSeconds = 0
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
        self.currentMinutes = (((readBuf[0] & 0x70) >> 4) * 10) + (readBuf[0] & 0x0F)
        self.currentMinutes = (((readBuf[1] & 0x70) >> 4) * 10) + (readBuf[1] & 0x0F)
        self.currentHours = (((readBuf[2] & 0x30) >> 4) * 10) + (readBuf[2] & 0x0F)
        self.currentWeekDay = readBuf[3]
        self.currentDay = (((readBuf[4] & 0x30) >> 4) * 10) + (readBuf[4] & 0x0F)
        self.currentMonth = (((readBuf[5] & 0x10) >> 4) * 10) + (readBuf[5] & 0x0F)
        self.currentYear = (((readBuf[6] & 0xF0) >> 4) * 10) + (readBuf[6] & 0x0F)

    # This actually pokes the time values into the RTC chip.
    # It converts the decimal values to BCD for the RTC chip
    def setTime(self, setHours, setMinutes, setSeconds):
        writeBuf = bytearray(2)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = self.STOP_RTC
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_HOURS_REG
        writeBuf[1] = (int(setHours / 10) << 4) | int(setHours % 10)
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_MINUTES_REG
        writeBuf[1] = (int(setMinutes / 10) << 4) | int(setMinutes % 10)
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)
        writeBuf[0] = self.RTC_SECONDS_REG
        writeBuf[1] = (
            self.START_RTC | (int(setSeconds / 10) << 4) | int(setSeconds % 10)
        )
        i2c.write(self.CHIP_ADDRESS, writeBuf, False)

    # These read functions only return the last read values.
    # use readValue() to update the stored numbers
    def seconds(self):
        clock.readValue()
        return self.currentMinutes

    def minutes(self):
        clock.readValue()
        return self.currentMinutes

    def hours(self):
        clock.readValue()
        return self.currentHours


# ==================== End of class KitronikRTC ====================
gc.collect()  # I know what this does, but not why Kiktronics example code needed it.

def resetLEDs():
    # Set all the LEDs to show a dim orange colour to start.
    # Note: Python ranges don't include the end value, so this will set 0-59
    for i in range(0, 60):
        halo_leds[i] = torchImage60x1[i]
        halo_leds.show()


# Initialise the Halo HD, which is basically a neopixel strip with 60 LEDs,
# plus a clock and a few other things.
halo_leds = NeoPixel(pin8, NUM_LEDS_ON_HALO)
clock = KitronikRTC()
clock.setTime(0, 0, 0)
previousMinutes = 0
minutesElapsed = 0
paused = False

resetLEDs()
while True:
    if accelerometer.was_gesture("shake"):
        # Reset the timer and LEDs, and unpause.
        previousMinutes = 0
        minutesElapsed = 0
        clock.setTime(0, 0, 0)
        resetLEDs()
        paused = False

    if accelerometer.was_gesture("face down"):
        paused = True

    if accelerometer.was_gesture("face up"):
        paused = False

    if button_a.was_pressed():
        #The torch buns out sooner! Tick the clock down by 10
        minutesElapsed += 10;
        if minutesElapsed > 60:
            minutesElapsed = 60;
        for i in range (0, minutesElapsed):
            halo_leds[i] = LED_BLACK
        halo_leds.show()

    if button_b.was_pressed():
        minutesElapsed -= 10;
        if minutesElapsed < 0:
            minutesElapsed = 0;
        clock.setTime(0, 0, 0)
        previousMinutes = 0
        minutesElapsed = 0
        paused = False
        resetLEDs()

    if paused:
        display.show(ICON_PAUSED)
    else:
        display.show(ICON_PLAY)
        currentMinutes = clock.minutes()
        if currentMinutes > previousMinutes:
            minutesElapsed += 1
            if minutesElapsed < 60:
                halo_leds[minutesElapsed] = LED_BLACK
                halo_leds.show()
                previousMinutes = currentMinutes
