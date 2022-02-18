#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: graph_airsens_bat.py  

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 18.02.2022 --> first prototype
"""
VERSION = '0.1.0'

import sys
import socket
import mysql.connector
import matplotlib.pyplot as plt

class AirSensBatGraph:
    
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
            if local_ip == self.server_ip: # if we are on the RPI with mysql server (RPI making temp acquis)
                # test the local database connection
                con = mysql.connector.connect(user=self.database_username, password=self.database_password, host=self.host_name, database=db)
            else:
                # test the distant database connection
                con = mysql.connector.connect(user=self.database_username, password=self.database_password, host=self.server_ip, database=db)
            return con, sys.exc_info()
        except:
            return False, sys.exc_info()

    def get_bat_data(self, local):
        
        db_connection, err = self.get_db_connection(self.database_name)
        db_cursor = db_connection.cursor()
        sql_txt = "SELECT time_stamp, temp, hum, pres, ubat FROM airsens WHERE local = '" + local + "';"
        db_cursor.execute(sql_txt)
        data = db_cursor.fetchall()
        x_data = [x[0] for x in data]
        temp_data = [y[1] for y in data]
        hum_data = [y[2] for y in data]
        pres_data = [y[3] for y in data]
        bat_data = [y[4] for y in data]
        
        return x_data, temp_data, hum_data, pres_data, bat_data

    def plot_air_data(self, local, l_names=None):
        # get data from db
        x, temp, hum, pres, ubat = self.get_bat_data(local)
        
        if l_names:
            label_val = l_names
        else:
            label_val = local
        
        figure, axis = plt.subplots(2, 2)
          
        # For Sine Function
        axis[0, 0].plot(x, temp)
        axis[0, 0].set_title("Température")
        axis[0, 0].grid(True)
          
        # For Cosine Function
        axis[0, 1].plot(x, hum)
        axis[0, 1].set_title("Humidité")
        axis[0, 1].grid(True)
          
        # For Tangent Function
        axis[1, 0].plot(x, pres)
        axis[1, 0].set_title("Pression atm.")
        axis[1, 0].grid(True)
          
        # For Tanh Function
        axis[1, 1].plot(x, ubat)
        axis[1, 1].set_title("Batterie")
        axis[1, 1].grid(True)
  
        # Combine all the operations and display
        figure.suptitle(label_val)
        plt.show()        # plot
        
    def main(self):
        locaux = ['sa', 'B9', 'ex']
        l_names = ['Salon', 'Bureau', 'Extérieur']
        for i, local in enumerate(locaux):
            self.plot_air_data(local, l_names[i])
        
if __name__ == '__main__':
    # instatiate the class
    airsens_bat_graph = AirSensBatGraph()
    # run main
    airsens_bat_graph.main()
 
