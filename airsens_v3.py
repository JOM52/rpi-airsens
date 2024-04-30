#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsens_v3_mqtt.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 19.08.2022 --> first prototype based on airsens_mqtt.py
v2.0.0 : 22.04.2023 --> adapté pour airsens_v2
v3.0.0 : 22.11.2023 --> adapté pour airsens_v3
"""
VERSION = '3.0.0'
APP = 'airsens_v3.py'

import paho.mqtt.client as mqtt
# import paho.mqtt.publish as publish
import time
import sys
import socket
import pymysql
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mqtt:

    def __init__(self):
        self.mariadb = MariaDb()
        # mqtt
        self.client = None
        self.mqtt_ip = '192.168.1.110'
        self.mqtt_topic = "airsens_v3"
        self.data_list = ['temp', 'hum', 'pres', 'gas', 'alt']
        self.data_format = ['{:.2f}', '{:.0f}', '{:.0f}', '{:.0f}', '{:.0f}']
        # BATTERY
        self.BAT_MAX = 4.2 # 100%
        self.BAT_MIN = 3.2 # 0%
        self.BAT_PENTE = (100-0)/(self.BAT_MAX - self.BAT_MIN)
        self.BAT_OFFSET = 100 - self.BAT_PENTE * self.BAT_MAX

    # This is the mqtt Subscriber
    def on_connect(self, client, userdata=None, flags=None, rc=None):
        print(APP + " V" + VERSION + " connected to mqtt topic " + client + " on " + self.mqtt_ip)
        print('--------------------------------------------------------------------------')
        self.client.subscribe(client)

    # This is the mqtt message manager
    def on_message(self, client, userdata, msg):
        # decode the message
        rx_msg = msg.payload.decode()
        topic, sensor_mac, sensor_name, sensor_type, measurements = rx_msg.split('/')
        measurements = measurements[1:-1]
        for mes in measurements.split(','):
            measure = mes.split(':')[0].strip().replace("'","")
            value = mes.split(':')[1].strip().replace("'","")
            self.mariadb.record_data_in_db(sensor_mac, sensor_name, sensor_type, measure, value)
            if measure == 'bat':
                t = time.localtime()
                current_datetime = time.strftime("%Y.%m.%d %H:%M:%S",t)
                print(current_datetime + ' ' + sensor_name + ' -> Battery: ' + value + 'V charge = ' + str(int(self.BAT_PENTE * float(value) + self.BAT_OFFSET)) + '%')

class MariaDb:
    
    def __init__(self):
        # database
        self.database_username = "pi"  # YOUR MYSQL USERNAME, USUALLY ROOT
        self.database_password = "mablonde"  # YOUR MYSQL PASSWORD
        self.host_name = "localhost"
        self.server_ip = '192.168.1.109'
        self.database_name = 'airsens'

    def get_db_connection(self, db):
        # get the local IP adress
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # verify if the mysql server is ok and the db avaliable
        try:
            if local_ip == self.server_ip:  # if we are on the RPI with mysql server
                # test the local database connection
                con = pymysql.connect(user=self.database_username, password=self.database_password,
                                              host=self.host_name, database=db)
            else:
                # test the distant database connection
                con = pymysql.connect(user=self.database_username, password=self.database_password,
                                              host=self.server_ip, database=db)
            return con, sys.exc_info()
        except:
            return False, sys.exc_info()

    def record_data_in_db(self, sensor_mac, sensor_name, sensor_type, measure, value):
        # insert the values in the db
        sql_txt = "".join(["INSERT INTO airsens_v3 (sensor_mac, sensor_name, sensor_type, measure, value) VALUES ('", \
                           sensor_mac, "',", "'", sensor_name, "',", "'", sensor_type, "',", "'", measure, "',", "'", value, "')"])
#         print(sql_txt)
        db_connection, err = self.get_db_connection(self.database_name)
        if db_connection:
            db_cursor = db_connection.cursor()
            db_cursor.execute(sql_txt)
            db_connection.commit()
            # close the db
            db_cursor.close()
            db_connection.close()
        else:
            print(err)

# class Email:
# 
#     def __init__(self):
#         # email
#         self.sender_address = 'esp32jmb@gmail.com'
#         self.sender_pass = 'wasjpwyjenoliobz'
#         self.receiver_address = 'jmetra@outlook.com'
#         self.mail_send = False
# 
#     def send_email(self, title, msg):
#         # Setup the MIME
#         message = MIMEMultipart()
#         message['From'] = self.sender_address
#         message['To'] = self.receiver_address
#         message['Subject'] = title
#         # The body and the attachments for the mail
#         message.attach(MIMEText(msg, 'plain'))
#         # Create SMTP session for sending the mail
#         session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
#         session.starttls()  # enable security
#         session.login(self.sender_address, self.sender_pass)  # login with mail_id and password
#         text = message.as_string()
#         session.sendmail(self.sender_address, self.receiver_address, text)
#         session.quit()
#         print('Mail Sent')


class AirSensNow:

    def __init__(self):
        self.mqtt = Mqtt()
#         self.email = Email()
    
    def main(self):
        # connect on the mqtt client
        self.mqtt.client = mqtt.Client()
        self.mqtt.client.connect(self.mqtt.mqtt_ip, 1883, 60)
        # mqtt interrup procedures
        self.mqtt.client.on_connect = self.mqtt.on_connect(self.mqtt.mqtt_topic)
        self.mqtt.client.on_message = self.mqtt.on_message
        # loop for ever
        self.mqtt.client.loop_forever()


if __name__ == '__main__':
    # instatiate the class
    airsens = AirSensNow()
    # run main
    airsens.main()

