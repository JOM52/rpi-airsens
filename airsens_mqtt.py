#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: mqtt_airsens.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 15.02.2022 --> first prototype
v0.1.1 : 16.02.2022 --> class created with the program
v0.1.2 : 01.06.2022 --> modified to limit number of mail send to 1
v0.1.3 : 01.06.2022 --> added proto-2
v0.1.4 : 10.06.2022 --> corrected battery voltage min and max
"""
VERSION = '0.1.1'
APP = 'airsens_mqtt'

import paho.mqtt.client as mqtt
import time
import sys
import socket
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def decode_msg(msg):
    # msg example: 'jmb10+2225599944476'
    jmb_id = msg[0:3]
    piece = msg[3:5]
    temp = int(msg[6:9]) / 10
    hum = int(msg[9:11])
    pres = int(msg[11:14])
    ubat = int(msg[14:17]) / 100
    rx_crc = msg[17:19]
    return jmb_id, piece, temp, hum, pres, ubat, rx_crc


def crc(msg):
    # calculate the crc of msg
    crc_0 = 0
    crc_1 = 0
    for i, char in enumerate(msg):
        if (i % 2) == 0:
            crc_0 += ord(char)
        else:
            crc_1 += ord(char)
    v_crc = crc_0 + crc_1 * 3
    if v_crc < 10:
        v_crc *= 10
    return str(v_crc)[-2:]


class AirSens:

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
        self.mqtt_topic = "airsens_test"

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
        _, local, temp, hum, pres, ubat, __ = decode_msg(rx_msg)
        # calculate % battery charge
        charge_bat = '{:4.1f}'.format((float(ubat) - self.UBAT_0) / ((self.UBAT_100 - self.UBAT_0) / 100))
        # insert the values in the db
        sql_txt = "".join(["INSERT INTO airsens (local, temp, hum, pres, ubat, charge_bat) VALUES ('",
                           local, "',",
                           "'", str(temp), "',",
                           "'", str(hum), "',",
                           "'", str(pres), "',",
                           "'", str(ubat), "',",
                           "'", str(charge_bat), "');"])
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
        return str_now, str_elapsed, charge_bat

    # This is the Subscriber
    def on_connect(self, client, userdata=None, flags=None, rc=None):
        print(APP + " V" + VERSION + " connected to mqtt topic " + client + " on " + self.mqtt_ip)
        print('--------------------------------------------------------------------------')
        self.client.subscribe(client)

    # This is the message manager
    def on_message(self, client, userdata, msg):
        # decode the message
        rx_msg = msg.payload.decode()
        # check the rx and calculate crc
        rx_crc = rx_msg[-2:]
        ctrl_crc = crc(rx_msg[:-2])
        if rx_crc == ctrl_crc:
            # decode the msg
            idx, local, temp, hum, pres, ubat, crc_v = decode_msg(rx_msg)
            # save the data in the db and get time, battery life and battery charge
            str_now, str_elapsed, charge_bat = self.record_data_in_db(rx_msg)
            # display the status for the sensor on battery
            if local == 'bu' or local == 'ex' or local == 'sa' or local == 'p0' or local == 'p2':
                str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
                if local == 'sa':
                    local_name = 'Salon :'
                elif local == 'bu':
                    local_name = 'Bureau:'
                elif local == 'ex':
                    local_name = 'Ext.  :'
                elif local == 'p0':
                    local_name = 'Proto-0 :'
                elif local == 'p2':
                    local_name = 'Proto-2 :'
                # build the message
                msg = local + ' - temp:' + '{:4.1f}'.format(temp) + '°C - hum:' + '{:2.0f}'.format(hum)
                msg += '% - pres:' + '{:3.0f}'.format(pres) + 'hPa - bat:' + '{:4.2f}'.format(ubat) + 'V'
                msg += ' - ' + local_name.upper() + ' - battery load:' + charge_bat + '%'
                msg += ' - battery life(j-h:m):' + str_elapsed
                msg += ' - ' + str_now
                print(msg)
                # check if the battery voltage is ok and send email if too low
                if float(ubat) < self.UBAT_0 and not self.mail_send:
                    title = local + ' --> time to recharge battery, tension = ' + str(ubat) + ' [V]'
                    print(title)
                    print('---------------------------------------------')
                    self.send_email(title, msg)
                    self.mail_send = True
            else:
                # just print the received values
                print(local
                      + ' - temp:' + '{:4.1f}'.format(temp) + '°C'
                      + ' - hum:' + '{:2.0f}'.format(hum) + '%'
                      + ' - pres:' + '{:3.0f}'.format(pres) + 'hPa'
                      + ' - bat:' + '{:4.2f}'.format(ubat) + 'V'
                      + ' - ' + str_now)
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
    airsens = AirSens()
    # run main
    airsens.main()
