#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsens_now_mqtt.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 19.08.2022 --> first prototype based on airsens_mqtt.py
"""
VERSION = '0.1.0'
APP = 'airsens_mqtt'

import paho.mqtt.client as mqtt
import time
import sys
import socket
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# def decode_msg(msg):
#     # msg example: 'jmb10+2225599944476'
#     jmb_id = msg[0:3]
#     piece = msg[3:5]
#     temp = int(msg[6:9]) / 10
#     hum = int(msg[9:11])
#     pres = int(msg[11:14])
#     ubat = int(msg[14:17]) / 100
#     rx_crc = msg[17:19]
#     return jmb_id, piece, temp, hum, pres, ubat, rx_crc
# 
# 
# def crc(msg):
#     # calculate the crc of msg
#     crc_0 = 0
#     crc_1 = 0
#     for i, char in enumerate(msg):
#         if (i % 2) == 0:
#             crc_0 += ord(char)
#         else:
#             crc_1 += ord(char)
#     v_crc = crc_0 + crc_1 * 3
#     if v_crc < 10:
#         v_crc *= 10
#     return str(v_crc)[-2:]


class AirSensNow:

    def __init__(self):
        # battery
        self.UBAT_100 = 4.5
        self.UBAT_0 = 3.0
        # database
        self.database_username = "pi"  # YOUR MYSQL USERNAME, USUALLY ROOT
        self.database_password = "mablonde"  # YOUR MYSQL PASSWORD
        self.host_name = "localhost"
        self.server_ip = '192.168.1.139'
        self.database_name = 'airsens'
        # email
        self.sender_address = 'esp32jmb@gmail.com'
        self.sender_pass = 'wasjpwyjenoliobz'
        self.receiver_address = 'jmetra@outlook.com'
        self.mail_send = False
        # mqtt
        self.mqtt_ip = '192.168.1.108'
        self.client = None
        self.mqtt_topic = "airsens_now_test"

    def get_db_connection(self, db):
        # get the local IP adress
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # verify if the mysql server is ok and the db avaliable
        try:
            if local_ip == self.server_ip:  # if we are on the RPI with mysql server (RPI making temp acquis)
                # test the local database connection
                con = mysql.connector.connect(user=self.database_username, password=self.database_password,
                                              host=self.host_name, database=db)
            else:
                # test the distant database connection
                con = mysql.connector.connect(user=self.database_username, password=self.database_password,
                                              host=self.server_ip, database=db)
            return con, sys.exc_info()
        except:
            return False, sys.exc_info()

    def send_email(self, title, msg):
        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = self.sender_address
        message['To'] = self.receiver_address
        message['Subject'] = title
        # The body and the attachments for the mail
        message.attach(MIMEText(msg, 'plain'))
        # Create SMTP session for sending the mail
        session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
        session.starttls()  # enable security
        session.login(self.sender_address, self.sender_pass)  # login with mail_id and password
        text = message.as_string()
        session.sendmail(self.sender_address, self.receiver_address, text)
        session.quit()
        print('Mail Sent')

    def record_data_in_db(self, rx_msg):
        # decode the rx_msg
#         print(rx_msg)
        _, local, temp, hum, pres, ubat = rx_msg.split(',')
        # insert the values in the db

#         print(str_now, '-', str_elapsed, '- ' + local
#               + ' - temp:' + '{:4.1f}'.format(float(temp)) + '°C'
#               + ' - hum:' + '{:2.1f}'.format(float(hum)) + '%'
#               + ' - pres:' + '{:3.1f}'.format(float(pres)) + 'hPa'
#               + ' - bat:' + '{:4.2f}'.format(float(ubat)) + 'V')
# 

        sql_txt = "".join(["INSERT INTO airsens (local, temp, hum, pres, ubat, charge_bat) VALUES ('",
                           local, "',",
                           "'", '{:4.2f}'.format(float(temp)), "',",
                           "'", '{:2.1f}'.format(float(hum)), "',",
                           "'", '{:3.1f}'.format(float(pres)), "',",
                           "'", '{:4.3f}'.format(float(ubat)), "',",
                           "'", str(0), "');"])
        db_connection, err = self.get_db_connection(self.database_name)
        db_cursor = db_connection.cursor()
        db_cursor.execute(sql_txt)
        db_connection.commit()
        # get the start time and date
        sql_duree_debut = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id ASC LIMIT 1;'
        db_cursor.execute(sql_duree_debut)
        date_start = db_cursor.fetchall()
        # get the end time and ddate
        sql_duree_fin = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id DESC LIMIT 1;'
        db_cursor.execute(sql_duree_fin)
        date_end = db_cursor.fetchall()
        # close the db
        db_cursor.close()
        db_connection.close()
        # calculate the battery life time
        str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
        elapsed = ((date_end[0][0] - date_start[0][0]).total_seconds())
        d = elapsed // (24 * 3600)
        elapsed = elapsed % (24 * 3600)
        h = elapsed // 3600
        elapsed %= 3600
        m = elapsed // 60
        elapsed %= 60
        str_elapsed = '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m))
        # return the calculate values
        return str_now, str_elapsed

    # This is the Subscriber
    def on_connect(self, client, userdata=None, flags=None, rc=None):
        print(APP + " V" + VERSION + " connected to mqtt topic " + client + " on " + self.mqtt_ip)
        print('--------------------------------------------------------------------------')
        self.client.subscribe(client)

    # This is the message manager
    def on_message(self, client, userdata, msg):
        # decode the message
        rx_msg = msg.payload.decode()
        _, local, temp, hum, pres, ubat = rx_msg.split(',')
        # save the data in the db and get time, battery life and battery charge
        str_now, str_elapsed = self.record_data_in_db(rx_msg)
        # display the status for the sensor on battery
        print(str_now, '-', str_elapsed, '- ' + local
              + ' - temp:' + '{:4.1f}'.format(float(temp)) + '°C'
              + ' - hum:' + '{:2.1f}'.format(float(hum)) + '%'
              + ' - pres:' + '{:3.1f}'.format(float(pres)) + 'hPa'
              + ' - bat:' + '{:4.2f}'.format(float(ubat)) + 'V')
    def main(self):
        # connect on the mqtt client
        self.client = mqtt.Client()
        self.client.connect(self.mqtt_ip, 1883, 60)
        # mqtt interrup procedures
        self.client.on_connect = self.on_connect(self.mqtt_topic)
        self.client.on_message = self.on_message
        # loop for ever
        self.client.loop_forever()


if __name__ == '__main__':
    # instatiate the class
    airsens = AirSensNow()
    # run main
    airsens.main()
