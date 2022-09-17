#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsensgraph_ext.py  

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
v0.1.6 : 06.06.2022 --> addeb battery life on graph
v0.1.7 : 12.09.2022 --> use dictonary for graph list
v0.2.0 : 16.09.2022 --> added day mean for temp, hum, pres
"""
import sys
import socket
import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pyautogui
import datetime

VERSION_NO = '0.2.0'
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
        self.filter = 30
        self.filter_day = int(24 * 60 / 5) # moyene sur mesure = 24h * 60m / 5m (intervalle)
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
        sql_txt = "SELECT time_stamp, temp, hum, pres, ubat FROM airsens WHERE local = '" + local + "' order by id desc;"
        db_cursor.execute(sql_txt)
        data = db_cursor.fetchall()
        x_data = [x[0] for x in data]
        temp_data = [y[1] for y in data]
        hum_data = [y[2] for y in data]
        pres_data = [y[3] for y in data]
        bat_data = [y[4] for y in data]

        return x_data, temp_data, hum_data, pres_data, bat_data
    
    def convert_sec_to_hms(self, seconds):
        min, sec = divmod(seconds, 60)
        hour, min = divmod(min, 60)
        return "%d:%02d" % (hour, min)

    def get_elapsed_time(self, local):
        
        db_connection, err = self.get_db_connection(self.database_name)
        db_cursor = db_connection.cursor()
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
        elapsed_s = ((date_end[0][0] - date_start[0][0]).total_seconds())
        elaps_hm = self.convert_sec_to_hms(elapsed_s)
        
        d = elapsed_s // (24 * 3600)
        elapsed_s = elapsed_s % (24 * 3600)
        h = elapsed_s // 3600
        elapsed_s %= 3600
        m = elapsed_s // 60
        elapsed_s %= 60
        str_elapsed = '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m))
        return str_elapsed, elaps_hm


    def plot_air_data(self, local, l_names, l_filter):
        
        plot_filtered_data = False
        if l_filter != 0:
            plot_filtered_data = True
            
        # get data from db
        time_x, temp, hum, pres, ubat = self.get_bat_data(local)
        if len(temp) ==0:
            return
        data_temp = {'time': time_x, 'temp': temp}
        data_hum = {'time': time_x, 'hum': hum}
        data_pres = {'time': time_x, 'pres': pres}
        data_bat = {'time': time_x, 'bat': ubat}
        
        df_temp = pd.DataFrame(data_temp)
        df_hum = pd.DataFrame(data_hum)
        df_pres = pd.DataFrame(data_pres)
        df_bat = pd.DataFrame(data_bat)

        f_temp = df_temp['temp'].rolling(window=l_filter).mean()
        f_hum = df_hum['hum'].rolling(window=l_filter).mean()
        f_pres = df_pres['pres'].rolling(window=l_filter).mean()
        f_bat = df_bat['bat'].rolling(window=l_filter).mean()

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
        ax1[0, 0].set_title("Température (en bleu moyenne journalière)")
        ax1[0, 0].grid(True)
        ax1[0, 0].plot(time_x, temp)
        if plot_filtered_data: ax1[0, 0].plot(np.array(time_x), np.array(f_temp), color='blue', zorder=5)

        # humidity
        ax1[0, 1].tick_params(labelrotation=45)
        ax1[0, 1].set_ylabel('[%]')
        ax1[0, 1].set_title("Humidité (en bleu moyenne journalière)")
        ax1[0, 1].grid(True)
        ax1[0, 1].plot(time_x, hum)
        if plot_filtered_data: ax1[0, 1].plot(np.array(time_x), np.array(f_hum), color='blue', zorder=5)

        # air pressure
        ax1[1, 0].tick_params(labelrotation=45)
        ax1[1, 0].set_ylabel('[hPa]')
        ax1[1, 0].set_title("Pression atm.  (en bleu moyenne journalière)")
        ax1[1, 0].grid(True)
        ax1[1, 0].plot(time_x, pres)
        if plot_filtered_data: ax1[1, 0].plot(np.array(time_x), np.array(f_pres), color='blue', zorder=5)

        #elapsed time
        elapsed, elaps_hm = self.get_elapsed_time(local)
        # battery voltage , filtered voltage and delta voltage in %
        ax1[1, 1].tick_params(labelrotation=45)
        ax1[1, 1].set_ylabel('[V]')
        ax1[1, 1].set_title("Tension batterie")
        ax1[1, 1].grid(True)
        ax1[1, 1].plot(time_x, ubat, color='lightsteelblue', zorder=0)

        #         ax1[1, 1].tick_params(axis ='y', labelcolor = 'blue')
        ax1[1, 1].plot(np.array(time_x), np.array(f_bat), color='red', zorder=5)
        legend1 = ax1[1, 1].legend(['U bat', 'U bat filtered on ' + str(self.filter) + ' measures'], loc='lower left')
        legend2 = ax1[1, 1].legend(['Vie batterie:[j-h:m] ' + elapsed + ' - [h:m] = ' + elaps_hm], loc='upper right')
        for item in legend2.legendHandles:
            item.set_visible(False)
        plt.gca().add_artist(legend1)
        plt.gca().add_artist(legend2)
        
        #elapsed time
        elapsed = self.get_elapsed_time(local)
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

        plt.show()  # plot

    def main(self):
        print('runing airsen_graph V' + VERSION_NO)
        """
        locaux{} is a dictionary with the structure:
        'key':[description, filter on n measures]
        n depend de l'intervalle entre deux mesures pour le filtrage se fass sur 24h
        exemple:
            intervalle de 5 min --> n = 24*60/5 = 288
            intervalle de 1 min --> n = 24*60/1 = 1440
        """
        locaux = {
#             '3a':['P03a: 2xAA = 3V intervalle = 1min',1440],
#             '3b':['P03b: 1S2P = 4.1V intervalle = 1min',1440],
#             '3c':['P03c: 3xAA = 4.5V intervalle = 1min',1440],
#             '4a':['P04a: 1S1P = 4.1V intervalle = 1min',1440],
#             'yc':['ESPnow Y03c: 3xAA = 4.5V intervalle = 1min',1440],
            'yx':['V-proxy-03c 1S1P = 4.1V intervalle variable',0],
            'ex':['Extérieur P04a: 4xAA = 6V intervalle=5min',288],
            'r1':['test durée p01a 1S1P=4.1V intervalle=1min',1440],
            'r2':['test durée p03a 1S2P=4.1V intervalle=1min',1440],
            'r4':['test durée p03c 3xAA=4.5V intervalle=1min',1440]
            }
        print('nbre_locaux:',len(locaux))
        for local in locaux.items():
            print('working for:', local[1])
            self.plot_air_data(local[0], local[1][0], local[1][1])
        print('end')

if __name__ == '__main__':
    # instantiate the class
    airsens_bat_graph = AirSensBatGraph()
    # run main
    airsens_bat_graph.main()
