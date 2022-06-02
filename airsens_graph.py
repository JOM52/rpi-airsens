#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: graph_airsens_bat.py  

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 18.02.2022 --> first prototype
v0.1.1 : 19.02.2022 --> added filtered voltage and delta % of the voltage
v0.1.2 : 19.02.2022 --> changed the calculation of d_bar scale (d_m)
v0.1.3 : 21.02.2022 --> grid for bat uniform for the 2 axes
v0.1.4 : 23.02.2022	--> adjusted the size of the graph the the whole screen
v0.1.5 : 02.06.2022 --> added local p2
"""
import sys
import socket
import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pyautogui

VERSION_NO = '0.1.4'
PROGRAM_NAME = 'airsens_graph.py'


class AirSensBatGraph:

    def __init__(self):
        # database
        self.database_username = "pi"  # YOUR MYSQL USERNAME, USUALLY ROOT
        self.database_password = "mablonde"  # YOUR MYSQL PASSWORD
        self.host_name = "localhost"
        self.server_ip = '192.168.1.139'
        self.database_name = 'airsens'
        # graph
        self.filter = 45
        self.reduce_y2_scale_factor = 2.5

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
        time_x, temp, hum, pres, ubat = self.get_bat_data(local)
        if len(temp) ==0:
            return
        data = {'time': time_x, 'bat': ubat}
        df = pd.DataFrame(data)

        f_bat = df['bat'].rolling(window=self.filter).mean()

        d_bat = pd.Series.diff(f_bat)
        d_bat = [b * 100 for b in d_bat]  # convert values in %
        data1 = {'time': time_x, 'bat': ubat, 'f_bat': f_bat, 'd_bat': d_bat}

        d_max = -1000
        d_min = 1000
        for d in d_bat:
            if d > d_max: d_max = d
            if d < d_min: d_min = d
        d_m = max(abs(d_max), abs(d_min)) * self.reduce_y2_scale_factor

        if l_names:
            label_val = l_names
        else:
            label_val = local

        fig, ax1 = plt.subplots(2, 2)

        # adjust the size of the graph to the screen
        screen_dpi = 90
        width, height = pyautogui.size()
        fig.set_figheight(height / screen_dpi)
        fig.set_figwidth(width / screen_dpi)

        # temperature

        ax1[0, 0].tick_params(labelrotation=45)
        ax1[0, 0].set_ylabel('[°C]')
        ax1[0, 0].set_title("Température")
        ax1[0, 0].grid(True)
        ax1[0, 0].plot(time_x, temp)

        # humidity
        ax1[0, 1].tick_params(labelrotation=45)
        ax1[0, 1].set_ylabel('[%]')
        ax1[0, 1].set_title("Humidité")
        ax1[0, 1].grid(True)
        ax1[0, 1].plot(time_x, hum)

        # air pressure
        ax1[1, 0].tick_params(labelrotation=45)
        ax1[1, 0].set_ylabel('[hPa]')
        ax1[1, 0].set_title("Pression atm.")
        ax1[1, 0].grid(True)
        ax1[1, 0].plot(time_x, pres)

        # battery voltage , filtered voltage and delta voltage in %
        ax1[1, 1].tick_params(labelrotation=45)
        ax1[1, 1].set_ylabel('[V]')
        ax1[1, 1].set_title("Tension batterie")
        ax1[1, 1].grid(True)
        ax1[1, 1].plot(time_x, ubat, color='lightsteelblue', zorder=0)

        #         ax1[1, 1].tick_params(axis ='y', labelcolor = 'blue')
        ax1[1, 1].plot(np.array(time_x), np.array(f_bat), color='red', zorder=5)
        ax1[1, 1].legend(['U bat', 'U bat filtered on ' + str(self.filter) + ' measures'], loc='lower left')

        # temporary not display the d(bat/dt) trace
        make_ax2 = False
        if make_ax2:
            ax2_color = 'wheat' #'sienna'
            ax2 = ax1[1, 1].twinx()
            ax2.tick_params(labelrotation=45)
            ax2.set_ylabel('d(bat/dt) [%]', color=ax2_color, zorder=10)
            ax2.plot(time_x, d_bat, color=ax2_color)
            ax2.tick_params(axis='y', labelcolor=ax2_color)
            ax2.legend(['delta ubat filtered %'], loc='upper right')
            ax2.set_ylim([-d_m, d_m])

        # Combine all the operations and display
        fig.suptitle(label_val.upper() + ' [' + PROGRAM_NAME + ' version:' + VERSION_NO + ']')
        plt.subplots_adjust(left=0.1,
                            bottom=0.1,
                            right=0.9,
                            top=0.9,
                            wspace=0.2,
                            hspace=0.4)
        plt.xticks(rotation=30)
        ax1[1, 1].set_yticks(
            np.linspace(ax1[1, 1].get_yticks()[0], ax1[1, 1].get_yticks()[-1], len(ax1[1, 1].get_yticks())))
        if make_ax2:
            ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1[1, 1].get_yticks())))

        plt.show()  # plot

    def main(self):
        print('runing airsen_graph V' + VERSION_NO)
        locaux = ['sa', 'bu', 'ex', 'p2']
        l_names = ['Salon', 'Bureau', 'Extérieur', 'Prototype p02']
        for i, local in enumerate(locaux):
            self.plot_air_data(local, l_names[i])

if __name__ == '__main__':
    # instantiate the class
    airsens_bat_graph = AirSensBatGraph()
    # run main
    airsens_bat_graph.main()
