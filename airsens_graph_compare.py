#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsens_graph_compare.py  

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
v0.2.1 : 18.09.2022 --> cosmetical changes
"""
import sys
import socket
import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pyautogui

VERSION_NO = '0.2.1'
PROGRAM_NAME = 'airsens_graph_compare.py'


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
        return '{:0d}'.format(int(hour))  + "h " + '{:0d}'.format(int(min)) + "m"

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
        elapsed_s = int((date_end[0][0] - date_start[0][0]).total_seconds())
        elaps_hm = self.convert_sec_to_hms(elapsed_s)
        elaps_s = elapsed_s
#         print((date_end[0][0] - date_start[0][0]).total_seconds())
#         print(elapsed_s)
        
        d = elapsed_s // (24 * 3600)
        elapsed_s = elapsed_s % (24 * 3600)
        h = elapsed_s // 3600
        elapsed_s %= 3600
        m = elapsed_s // 60
        elapsed_s %= 60
        str_elapsed = '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m))
        str_elapsed = '{:02d}'.format(int(d)) + 'j ' + '{:2d}'.format(int(h)) + 'h ' + '{:2d}'.format(int(m)) + 'm'
        return str_elapsed, elaps_hm, elaps_s

    def plot_compare(self, locaux):
        
        plot_filtered_data = False
        
        fig, ax1 = plt.subplots(2, 1)
        # adjust the size of the graph to the screen
        screen_dpi = 90
        width, height = pyautogui.size()
        fig.set_figheight(height / screen_dpi)
        fig.set_figwidth(width / screen_dpi)
        
        color = ['black', 'red', 'brown', 'green', 'blue']
#         legend_txt = ''
        font = {'family': 'serif', 'color':  'darkred', 'weight': 'normal', 'size': 16,}
        
        for i, local_d in enumerate(locaux.items()):
            
            local = local_d[0]
            local_detail = local_d[1][0]
            l_filter = local_d[1][1]
            print('working for:', str(local_d[0]) + ' - ' + str(local_d[1]))
            # get data from db
            time_x, temp, hum, pres, ubat = self.get_bat_data(local)
            if len(temp) ==0:
                return
            data_temp = {'time': time_x, 'temp': temp}
            data_hum = {'time': time_x, 'hum': hum}
            data_pres = {'time': time_x, 'pres': pres}
            data_bat = {'time': time_x, 'bat': ubat}
            
            dataframe_temp = pd.DataFrame(data_temp)
            dataframe_hum = pd.DataFrame(data_hum)
            dataframe_pres = pd.DataFrame(data_pres)
            dataframe_bat = pd.DataFrame(data_bat)

            filtered_temp = dataframe_temp['temp'].rolling(window=l_filter).mean()
            filtered_hum = dataframe_hum['hum'].rolling(window=l_filter).mean()
            filtered_pres = dataframe_pres['pres'].rolling(window=l_filter).mean()
            filtered_bat = dataframe_bat['bat'].rolling(window=l_filter).mean()

            # temperature
            ax1[0].tick_params(labelrotation=45)
            ax1[0].set_ylabel('[°C]')
            ax1[0].grid(True)
            if not plot_filtered_data: ax1[0].plot(time_x, temp, color=color[i], label=local + ': ' + local_d[1][0])
            if plot_filtered_data: ax1[0].plot(np.array(time_x), np.array(filtered_temp), color=color[i], zorder=5,
                                               label=local + ': ' + local_d[1][0])

            # humidity
            ax1[1].tick_params(labelrotation=45)
            ax1[1].set_ylabel('[%]')
            ax1[1].set_title("Humidité")
            ax1[1].grid(True)
            if not plot_filtered_data: ax1[1].plot(time_x, hum, color=color[i])
            if plot_filtered_data: ax1[1].plot(np.array(time_x), np.array(filtered_hum), color=color[i], zorder=5,
                                               label=local + ': ' + local_d[1][0])
            
        fig.legend(loc='center right')#, title=local + ': ' + local_d[1][0])
            
        fig.suptitle(PROGRAM_NAME + ' ' + VERSION_NO)
        plt.subplots_adjust(left=0.1,
                            bottom=0.1,
                            right=0.9,
                            top=0.9,
                            wspace=0.2,
                            hspace=0.4)
        plt.xticks(rotation=30)
        ax1[1].set_yticks(
            np.linspace(ax1[1].get_yticks()[0], ax1[1].get_yticks()[-1], len(ax1[1].get_yticks())))
#         x_center = elaps_s // 2
#         ax1[0, 0].text(x_center, 10, legend_txt, fontdict=font)
        plt.show()  # plot

    def main(self):
        print('runing airsen_graph V' + VERSION_NO)
        """
        locaux{} is a dictionary with the structure:
        'key':[description, average on n measures]
        n depend de l'intervalle entre deux mesures pour que la moyenne soit sur 24h
        si n=0  pas de print de la courbe moyenne autrement exemple:
            intervalle de 5 min --> n = 24*60/5 = 288
            intervalle de 1 min --> n = 24*60/1 = 1440
            intervalle de 15 min --> m = 24*60/15 = 96
        """
        locaux = {
#             '3a':['P03a: 2xAA = 3V intervalle = 1min',1440],
#             '3b':['P03b: 1S2P = 4.1V intervalle = 1min',1440],
#             '3c':['P03c: 3xAA = 4.5V intervalle = 1min',1440],
#             '4a':['P04a: 1S1P = 4.1V intervalle = 1min',1440],
#             'yc':['ESPnow Y03c: 3xAA = 4.5V intervalle = 1min',1440],
#             'yx':['V-proxy-03c 1S1P = 4.1V intervalle variable',0],
#             'ex':['Extérieur P04a: 4xAA=6V intervalle=5min',288],
#             'r1':['test durée p01a 1S1P=4.1V intervalle=1min',1440],
#             'r2':['test durée p03a 1S2P=4.1V intervalle=1min',1440],
#             'r4':['test durée p03c 3xAA=4.5V intervalle=1min',1440],
#             '5a':['Extérieur: bme280 1S2P Li-Ion 15min',96],
#             'tld_06c':['Extérieur: bme280 1S2P Li-Ion 5min',288],
#             'tld_06d':['Extérieur: bme280 1S2P Li-Ion 5min',288],
#             'hdc1080':['Bureau hdc1080: USB=5V intervalle=5min',288],
#             'Sensor':['Bureau: hdc1080 1S1P Li-Ion 5min',288],
            'First_1':['Bureau: hdc1080 1S1P Li-Ion 5min',288],
            'Sensor':['hdc1080 5min',288],
            'First_2':['hdc1080 5min',288],
#             'xx_bme280':['bme280 1min',1440],
#             'xx_bme680':['bme680 1min',1440],
#             'xx_hdc1080':['hdc1080 1min',1440],
            }
        print('nbre_locaux:',len(locaux))
        self.plot_compare(locaux)

if __name__ == '__main__':
    # instantiate the class
    airsens_bat_graph = AirSensBatGraph()
    # run main
    airsens_bat_graph.main()
