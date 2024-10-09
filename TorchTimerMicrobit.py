from microbit import *
from neopixel import NeoPixel
import gc
from time import sleep_ms

global clock
global halo_leds
global torch_image
global light_images

# Some constants
NUM_LEDS_ON_HALO = 60

ICON_PLAY = Image("09000:09900:09990:09900:09000")
ICON_PAUSED = Image("99099:99099:99099:99099:99099")
ICON_FINISHED = Image("90009:09090:00900:09090:90009")

BLACK = (0, 0, 0)

S1 = (8, 8, 8)
S2 = (10, 10, 10)
S3 = (12, 12, 12)
S4 = (14, 14, 14)

T4 = (22, 14,  0)
T3 = (20, 12,  0)
T2 = (20, 10,  0)
T1 = (18,  8,  0)


torch01 = [T3, T3, T2, T2, T1, T2, T2, T2, T3, T3,
           T3, T3, T2, T2, T1, T2, T2, T2, T3, T3,
           T3, T3, T2, T2, T1, T2, T2, T2, T3, T3,
           T3, T3, T2, T2, T1, T2, T2, T2, T3, T3,
           T3, T3, T2, T2, T1, T2, T2, T2, T3, T3,
           T3, T3, T2, T2, T1, T2, T2, T2, T3, T3]

torch02 = [T2, T2, T2, T2, T2, T2, T2, T2, T2, T2,
           T2, T2, T2, T2, T2, T2, T2, T2, T2, T2,
           T2, T2, T2, T2, T2, T2, T2, T2, T2, T2,
           T2, T2, T2, T2, T2, T2, T2, T2, T2, T2,
           T2, T2, T2, T2, T2, T2, T2, T2, T2, T2,
           T2, T2, T2, T2, T2, T2, T2, T2, T2, T2]

torch03 = [T1, T2, T2, T3, T4, T3, T3, T2, T2, T1,
           T1, T2, T2, T3, T4, T3, T3, T2, T2, T1,
           T1, T2, T2, T3, T4, T3, T3, T2, T2, T1,
           T1, T2, T2, T3, T4, T3, T3, T2, T2, T1,
           T1, T2, T2, T3, T4, T3, T3, T2, T2, T1,
           T1, T2, T2, T3, T4, T3, T3, T2, T2, T1]

spell01 = [S1, S2, S3, S2, S1, S1, S1, S1, S1, S2,
           S3, S2, S2, S3, S1, S1, S2, S1, S2, S3,
           S3, S2, S3, S2, S1, S1, S2, S2, S1, S2,
           S2, S3, S2, S1, S2, S2, S3, S2, S3, S2,
           S1, S1, S2, S1, S2, S2, S3, S4, S3, S2,
           S1, S2, S2, S3, S2, S1, S1, S2, S1, S1]

spell02 = [S1, S1, S2, S3, S2, S1, S2, S2, S1, S1,
           S3, S2, S2, S3, S1, S1, S2, S1, S2, S2,
           S2, S2, S3, S2, S1, S1, S2, S2, S1, S2,
           S2, S3, S2, S1, S2, S2, S3, S2, S3, S2,
           S2, S1, S2, S1, S2, S2, S3, S2, S3, S2,
           S2, S2, S3, S3, S2, S1, S2, S1, S1, S2]

spell03 = [S2, S2, S3, S2, S1, S2, S3, S4, S3, S2,
           S2, S1, S2, S2, S2, S1, S2, S1, S2, S2,
           S1, S2, S3, S2, S2, S1, S2, S2, S1, S2,
           S1, S2, S1, S1, S2, S2, S3, S2, S3, S2,
           S2, S1, S2, S1, S2, S2, S3, S4, S3, S2,
           S1, S1, S2, S2, S1, S2, S3, S2, S2, S3]

torch_images = [torch01, torch02, torch03]
spell_images = [spell01, spell02, spell03]

light_images = torch_images


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

def set_LEDs(num_extinguished):
    if num_extinguished > 0:
        for i in range(0, num_extinguished):
            halo_leds[i] = BLACK
    if num_extinguished < 60:
        for i in range(num_extinguished, 60):
            halo_leds[i] = torch_image[i]
    halo_leds.show()

def resetTorch():
    clock.setTime(0, 0, 0)  # This also unpauses it
    set_LEDs(0)
    gc.collect()


# Initialise the Halo HD, which is basically a neopixel strip with 60 LEDs,
# plus a clock and a few other things.
halo_leds = NeoPixel(pin8, NUM_LEDS_ON_HALO)
clock = KitronikRTC()
animation_counter = 0
animation_step = 1
animation_paused = False
torch_image = light_images[animation_counter]
resetTorch()


while True:
    if microphone.current_event() == SoundEvent.LOUD:
        if light_images == torch_images:
            light_images = spell_images
        else:
            light_images = torch_images

    if accelerometer.was_gesture("shake"):
        # Reset the timer and LEDs, and unpause.
        resetTorch()

    if accelerometer.was_gesture("face down"):
        clock.pause()

    if accelerometer.was_gesture("face up"):
        clock.unpause()

    clock.readValue()

    if pin_logo.is_touched():
        animation_paused = not animation_paused

    if button_a.was_pressed():
        clock.addMinutes(10)
        clock.readValue()

    if button_b.was_pressed():
        clock.addMinutes(-10)
        clock.readValue()

    minutes_elapsed = clock.minutes
    if clock.hourHasElapsed():
        minutes_elapsed = 60

    if clock.hourHasElapsed():
        display.show(ICON_FINISHED)
    elif clock.paused:
        display.show(ICON_PAUSED)
    else:
        display.show(ICON_PLAY)

    if not animation_paused:
        animation_counter += animation_step
        if (0 == animation_counter) or ((len(light_images) - 1) == animation_counter):
            animation_step *= -1
        torch_image = light_images[animation_counter]
    set_LEDs(minutes_elapsed)
    sleep_ms(100)
