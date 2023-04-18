#!/usr/bin/python
# -*- coding: UTF-8 -*-

#
#    this is an UART-LoRa device and thers is an firmware on Module
#    users can transfer or receive the data directly by UART and dont
#    need to set parameters like coderate,spread factor,etc.
#    |============================================ |
#    |   It does not suport LoRaWAN protocol !!!   |
#    | ============================================|
#   
#    This script is mainly for Raspberry Pi 3B+, 4B, and Zero series
#    Since PC/Laptop does not have GPIO to control HAT, it should be configured by
#    GUI and while setting the jumpers, 
#    Please refer to another script pc_main.py
#

import sys
import sx126x
import threading
import time
import select
import termios
import tty
from bmp280 import BMP280
import RPi.GPIO as GPIO

try: 
	from smbus2 import SMBus
except ImportError:
	from smbus import SMBus

import board
import busio
import adafruit_sgp30

from threading import Timer

#Buzzer
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(17,GPIO.OUT)

#BMP280
bus = SMBus(1)
bmp280 =BMP280(i2c_dev=bus)

#SGP30
i2c = busio.I2C(board.SCL, board.SDA)

sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

sgp30.set_iaq_baseline(0x8973,0x8AAE)
sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)

elapsed_sec=0

#
#    Need to disable the serial login shell and have to enable serial interface 
#    command `sudo raspi-config`
#    More details: see https://github.com/MithunHub/LoRa/blob/main/Basic%20Instruction.md
#
#    When the LoRaHAT is attached to RPi, the M0 and M1 jumpers of HAT should be removed.
#

# node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=868,addr=0,power=22,rssi=True,air_speed=2400,relay=False)

def send_deal():
	get_rec = ""
#    print("input a string such as \033[1;32m0,868,Hello World\033[0m,it will send `Hello World` to lora node device of address 0 with 868M ")
#    print("please input and press Enter key:",end='',flush=True)

#    while True:
#        rec = sys.stdin.read(1)
#        if rec != None:
#            if rec == '\x0a': break
#            get_rec += rec
#            sys.stdout.write(rec)
#            sys.stdout.flush()

	# Medir temperatura
	temperature = bmp280.get_temperature()
	# Medir presion
	pressure = bmp280.get_pressure()
	# Medir altitud
	altitude = bmp280.get_altitude(qnh = 1022)
	# Medir CO2
	eCO2 = sgp30.eCO2
	tvoc = sgp30.TVOC
#	eCO2 = 0
#	tvoc = 0
	
	mensaje = "Altitud: "+str(altitude)+";"+"Temperatura: "+str(temperature)+";"+"Presion: "+str(pressure)+"\n"+"CO2: " + str(eCO2) + "; TVOC: " + str(tvoc)
	# Información que se envia
	payload = str(altitude)+";"+str(temperature)+";"+str(pressure)+";"+str(eCO2)+";"+str(tvoc)
	print(mensaje)
	get_rec = "0,868,"+ payload
	get_t = get_rec.split(",")
	
	offset_frequence = int(get_t[1])-(850 if int(get_t[1])>850 else 410)
    #
    # the sending message format
    #
    #         receiving node              receiving node                   receiving node           own high 8bit           own low 8bit                 own 
    #         high 8bit address           low 8bit address                    frequency                address                 address                  frequency             message payload
	data = bytes([int(get_t[0])>>8]) + bytes([int(get_t[0])&0xff]) + bytes([offset_frequence]) + bytes([node.addr>>8]) + bytes([node.addr&0xff]) + bytes([node.offset_freq]) + get_t[2].encode()
	
	node.send(data)
	
	# TODO: Guardar datos en archivo local en raspberry PI

print("Iniciando CANSAT")
print("Transmitiendo datos...")

while True:
	GPIO.output(17,GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(17,GPIO.LOW)
	time.sleep(0.5)
	send_deal()
