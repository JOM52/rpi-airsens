# acquisitions
SENSOR_LOCATION = 'First_1' 
T_DEEPSLEEP_MS = 300000
# sensor
# SENSOR_TYPE = 'bme280'
SENSOR_TYPE = 'hdc1080'
# power supply
ON_BATTERY = True
UBAT_100 = 4.1
UBAT_0 = 3.2
# I2C hardware config
BME_SDA_PIN = 21
BME_SCL_PIN = 22
# analog voltage measurement
R1 = 997000 # first divider bridge resistor
R2 = 323000 # second divider bridge resistor
DIV = R2 / (R1 + R2)  
ADC1_PIN = 35 # Measure of analog voltage (ex: battery voltage following)
#averaging of measurements
AVERAGING_BAT = 5
AVERAGING_BME = 5
# ESP-now
# PROXY_MAC_ADRESS = b'<a\x05\rg\xcc'
PROXY_MAC_ADRESS = b'<a\x05\x0c\xe7('


