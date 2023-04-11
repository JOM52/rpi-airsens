# acquisitions
SENSOR_LOCATION = 'v2_' 
T_DEEPSLEEP_MS = 15000
# sensor
SENSORS = {
    'hdc1080': ['temp', 'hum'],
#     'bme280': ['temp', 'hum', 'pres'],
#     'bme680': ['temp', 'hum', 'pres', 'gas', 'alt']
    }
# power supply
ON_BATTERY = True
UBAT_100 = 4.1
UBAT_0 = 3.2
# I2C hardware config
BME_SDA_PIN = 21
BME_SCL_PIN = 22
# analog voltage measurement
R1 = 977000 # first divider bridge resistor
R2 = 312000 # second divider bridge resistor
DIV = R2 / (R1 + R2)  
ADC1_PIN = 35 # Measure of analog voltage (ex: battery voltage following)
#averaging of measurements
AVERAGING_BAT = 1
AVERAGING_BME = 1
# ESP-now
PROXY_MAC_ADRESS = b'<a\x05\rg\xcc'
# PROXY_MAC_ADRESS = b'<a\x05\x0c\xe7('


