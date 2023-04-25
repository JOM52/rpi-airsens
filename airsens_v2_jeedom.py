#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsens_now_mqtt.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 19.08.2022 --> first prototype based on airsens_mqtt.py
v2.0.0 : 22.04.2023 --> adapté pour airsens_v2
"""
VERSION = '2.0.0'
APP = 'airsens_v2_mqtt'

import paho.mqtt.client as mqtt
# import paho.mqtt.publish as publish
import time
import sys
import socket
import mysql.connector
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



class AirSensNow:

    def __init__(self):
        self.mqtt = Mqtt()
        self.email = Email()
    
    def main(self):
        # connect on the mqtt client
        self.mqtt.client = mqtt.Client()
        self.mqtt.client.connect(self.mqtt.mqtt_ip, 1883, 60)
        # mqtt interrup procedures
        self.mqtt.client.on_connect = self.mqtt.on_connect(self.mqtt.mqtt_topic_v2)
        self.mqtt.client.on_message = self.mqtt.on_message
        # loop for ever
        self.mqtt.client.loop_forever()

class Mqtt:

    def __init__(self):
        self.mariadb = MariaDb()
        # mqtt
        self.mqtt_ip = '192.168.1.108'
        self.client = None
        self.mqtt_topic_v2 = "airsens_v2"
#         self.mqtt_topic_domoticz = "airsens_domoticz"
        self.mqtt_topic_jeedom = "airsens_jeedom"
        self.data_list = ['temp', 'hum', 'pres', 'gas', 'alt']

    # This is the Subscriber
    def on_connect(self, client, userdata=None, flags=None, rc=None):
        print(APP + " V" + VERSION + " connected to mqtt topic " + client + " on " + self.mqtt_ip)
        print('--------------------------------------------------------------------------')
        self.client.subscribe(client)

    # This is the message manager
    def on_message(self, client, userdata, msg):
        # decode the message
        rx_msg = msg.payload.decode()
        print(rx_msg)
        _, local, data, rssi = rx_msg.split(',')
        
        data = data[1:len(data)-1].split(':')
        for i, d in enumerate(data):
            if i < len(data) - 1:
                record = (local, self.data_list[i], d)
            else:
                record = (local, 'bat', d)
            # store data in db
            now, elapsed = self.mariadb.record_data_in_db(record)
            # send data to domoticz
            topic = ''.join([self.mqtt_topic_jeedom, '/', local , '/', record[1]])
            payload = d
            hostname = self.mqtt_ip
            client.publish(topic, payload)
#             publish.single(topic, payload, hostname=self.mqtt_ip)


class MariaDb:
    
    def __init__(self):
        # database
        self.database_username = "pi"  # YOUR MYSQL USERNAME, USUALLY ROOT
        self.database_password = "mablonde"  # YOUR MYSQL PASSWORD
        self.host_name = "localhost"
        self.server_ip = '192.168.1.139'
        self.database_name = 'airsens'

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

    def record_data_in_db(self, rx_msg):
        # decode the rx_msg
        # insert the values in the db
        sql_txt = "".join(["INSERT INTO airsens_v2 (loc, name, val) VALUES ('", rx_msg[0], "',", "'", rx_msg[1], "',", "'", rx_msg[2], "')"])
#         print(sql_txt)
        db_connection, err = self.get_db_connection(self.database_name)
        db_cursor = db_connection.cursor()
        db_cursor.execute(sql_txt)
        db_connection.commit()
        # get the start time and date
        sql_duree_debut = 'SELECT time_stamp FROM airsens_v2 WHERE loc="' + rx_msg[0] + '" ORDER BY id ASC LIMIT 1;'
        db_cursor.execute(sql_duree_debut)
        date_start = db_cursor.fetchall()
        # get the end time and ddate
        sql_duree_fin = 'SELECT time_stamp FROM airsens_v2 WHERE loc="' + rx_msg[0] + '" ORDER BY id DESC LIMIT 1;'
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
#         print(str_now, str_elapsed)
        return str_now, str_elapsed

class Email:

    def __init__(self):
        # email
        self.sender_address = 'esp32jmb@gmail.com'
        self.sender_pass = 'wasjpwyjenoliobz'
        self.receiver_address = 'jmetra@outlook.com'
        self.mail_send = False

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


if __name__ == '__main__':
    # instatiate the class
    airsens = AirSensNow()
    # run main
    airsens.main()
