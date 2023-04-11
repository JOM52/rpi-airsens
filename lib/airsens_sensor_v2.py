#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
file: airsens_sensor_multi.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-airsens-now

The sensors are made with an ESP32 microcontroller and can be powered by battery or by USB.
They transmit the data to a central also realized with an ESP32 by a ESPnow interface

v0.1.0 : 17.08.2022 --> first prototype based on airsens_ble_sensor.py
----------------------------------------------------------------------
v0.2.0 : 07.09.2022 --> modified for new log_and_count.py version ---> no more compatible with previous versions
v0.2.1 : 07.09.2022 --> espnow and wifi powered off before going to deepsleep
v0.2.2 : 19.12.2022 --> small cosmetices changes
v0.2.3 : 20.12.2022 --> temporary change for develop proxy display
v0.2.4 : 03.01.2022 --> added fake sensor for test
v0.2.5 : 11.01.2023 --> name of the conf file modified to airsens_now_sensor_display_conf.py
v0.3.0 : 17.02.2023 --> new version for long time test (tld)
v0.3.1 : 26.02.2023 --> usage of conf values simplidied
----------------------------------------------------------------------
v1.0.0 : 12.03.2023 --> First production version - one version for bme280 and hdc1080
----------------------------------------------------------------------
v2.0.0 : 02.04.2023 --> New data concept
"""
from utime import ticks_ms, sleep_ms
start_time = ticks_ms()
# PARAMETERS ========================================
PRG_NAME = 'airsens_sensor_v2.py'
PRG_VERSION = '2.0.0'
import airsens_sensor_conf_v2 as conf  # configuration file
from machine import Pin, freq, TouchPad
from machine import ADC, SoftI2C, deepsleep
from sys import exit
from lib.log_and_count import LogAndCount
log = LogAndCount()
if 'bme280' in conf.SENSORS:
    import lib.bme280 as bme280
if 'bme680' in conf.SENSORS:
    import lib.bme680 as bme680
if 'hdc1080' in conf.SENSORS:
    import lib.hdc1080 as hdc1080
from network import WLAN, STA_IF
from espnow import  ESPNow

pot = ADC(Pin(conf.ADC1_PIN))            
pot.atten(ADC.ATTN_6DB ) # Umax = 2V
pot.width(ADC.WIDTH_12BIT) # 0 ... 4095

def main():
    
    try:
        print('=================================================')
        print(PRG_NAME + ' - ' + PRG_VERSION + '\n')
        i = log.counters('passe', True)

        # instanciation of I2C
        i2c = SoftI2C(scl=Pin(conf.BME_SCL_PIN), sda=Pin(conf.BME_SDA_PIN), freq=10000)

        # instanciation of sensor
        measurements = []
        for sensor_actif in conf.SENSORS:
            if sensor_actif == 'bme280':
                sensor = bme280.BME280(i2c=i2c)
            elif sensor_actif == 'bme680':
                sensor = bme680.BME680_I2C(i2c=i2c)
            elif sensor_actif == 'hdc1080':
                sensor = hdc1080.HDC1080(i2c=i2c)
            
            measurement_list = conf.SENSORS.get(sensor_actif)
            for measurement in measurement_list:
                value = 0
                for l in range(conf.AVERAGING_BME):
                    if measurement == 'temp':
                        value += float(sensor.temperature)
                    elif measurement == 'pres':
                        value += float(sensor.pressure)
                    elif measurement == 'hum':
                        value += float(sensor.humidity)
                    elif measurement == 'gas':
                        value += float(sensor.gas)
                    elif measurement == 'alt':
                        value += float(sensor.altitude)
                value = str(value / conf.AVERAGING_BME)
                measurements.append('jmb,' + conf.SENSOR_LOCATION + sensor_actif + ',' + measurement + ',' + value)

            # read the battery voltage
            bat = 0
            for l in range(conf.AVERAGING_BAT):
                bat += pot.read()
            bat = str(bat / conf.AVERAGING_BAT * (2 / 4095) / conf.DIV)
            measurements.append('jmb,' + conf.SENSOR_LOCATION + sensor_actif + ',' + 'bat' + ',' + bat)
    
        # A WLAN interface must be active to send()/recv()
        sta = WLAN(STA_IF)
        sta.active(True)
        # instantiation of ESPNow
        espnow = ESPNow()
        espnow.active(True)
        espnow.add_peer(conf.PROXY_MAC_ADRESS)
        # send the message
        for msg in measurements:
            print(msg)
            espnow.send(msg)
        # close the communication canal
        espnow.active(False)
        espnow = None
        sta.active(False)
        sta = None
        # prepare for deepsleep
        total_time = ticks_ms() - start_time
        t_deepsleep = max(conf.T_DEEPSLEEP_MS - total_time, 10)
        # check the level of the battery
        if float(bat) > conf.UBAT_0 or not conf.ON_BATTERY:
            # battery is ok so finishing tasks
            print('passe', i, '- error count:', log.counters('error', False),'-->' , str(total_time) + 'ms')
            print('going to deepsleep for: ' + str(t_deepsleep) + ' ms')
            print('=================================================')
            deepsleep(t_deepsleep)
        else:
            # battery is dead so endless sleep to protect the battery
            pass_to_wait = 10
            for i in range(pass_to_wait):
                print('going to endless deepsleep in ' + str(pass_to_wait - i) + ' s')
                sleep_ms(1000)
            print('Endless deepsleep due to low battery')
            deepsleep()
        
    except Exception as err:
        log.counters('error', True)
        log.log_error('airsens_sensor main error', log.error_detail(err))
        print('going to deepsleep for: ' + str(conf.T_DEEPSLEEP_MS) + ' ms')
        deepsleep(conf.T_DEEPSLEEP_MS)

if __name__ == "__main__":
    main()
