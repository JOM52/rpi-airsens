#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsens_graph_batt.py  

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 18.0t.2022 --> first prototype based on airsens_graph
v0.1.1 : 26.07.2022 --> added algorithm for multi graphs placement
v0.1.2 : 12.09.2022 --> use dictonary for graph list
v0.2.0 : 16.09.2022 --> added day mean for temp, hum, pres
v0.2.1 : 17.09.2022 --> cosmetical changes
v0.2.2 : 12.10.2024 --> ajouté valeur moyenne dans entête du graphique
"""
import sys
import socket
import mysql.connector
import matplotlib.pyplot as plt
import pandas as pd
# import numpy as np
import pyautogui
import math

VERSION_NO = '0.2.1'
PROGRAM_NAME = 'airsens_graph_batt.py'
MYSQL_SERVER = '192.168.1.165'


class AirSensBatGraph:

    def __init__(self):
        # database
        self.database_username = "pi"  # YOUR MYSQL USERNAME, USUALLY ROOT
        self.database_password = "mablonde"  # YOUR MYSQL PASSWORD
        self.host_name = "localhost"
        self.server_ip = MYSQL_SERVER
        self.database_name = 'airsens'
        # graph
        self.filter = 60
        self.intervalle = 60 # intervalle entre deux mesures
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
        if not db_connection:
            print('\nDB connection error')
            print(err)
            exit()
        db_cursor = db_connection.cursor()
        sql_txt = "select time_stamp, value from airsens_v3 where sensor_name ='" + local + "' and measure='bat' order by id;"

        db_cursor.execute(sql_txt)
        data = db_cursor.fetchall()
        x_data = [x[0] for x in data]
        bat_data = [y[1] for y in data]

        return x_data, bat_data
    
    def convert_sec_to_hms(self, seconds):
        min, sec = divmod(seconds, 60)
        hour, min = divmod(min, 60)
        return str(int(hour)) + 'h' + str(int(min)) + 'm'

    def get_elapsed_time(self, local):
        
        db_connection, err = self.get_db_connection(self.database_name)
        if not db_connection:
            print('\nDB connection error')
            print(err)
            exit()
        db_cursor = db_connection.cursor()
        # get the start time and date
#         sql_duree_debut = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id ASC LIMIT 1;'
        sql_duree_debut = "select time_stamp from airsens_v3 where sensor_name ='" + local + "' and measure='bat' order by id asc limit 1;"
        db_cursor.execute(sql_duree_debut)
        date_start = db_cursor.fetchall()
        # get the end time and ddate
#         sql_duree_fin = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id DESC LIMIT 1;'
        sql_duree_fin = "select time_stamp from airsens_v3 where sensor_name ='" + local + "' and measure='bat' order by id desc limit 1;"
        db_cursor.execute(sql_duree_fin)
        date_end = db_cursor.fetchall()
        # close the db
        db_cursor.close()
        db_connection.close()
        # calculate the battery life time
#         print(date_start, date_end)
        elapsed_s = ((date_end[0][0] - date_start[0][0]).total_seconds())
        
        elaps_hm = self.convert_sec_to_hms(elapsed_s)
        
        d = elapsed_s // (24 * 3600)
        elapsed_s = elapsed_s % (24 * 3600)
        h = elapsed_s // 3600
        elapsed_s %= 3600
        m = elapsed_s // 60
        elapsed_s %= 60
        str_elapsed = '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m))
        str_elapsed = str(int(d)) + 'j' + str(int(h)) + 'h' + str(int(m)) + 'm'
        return str_elapsed, elaps_hm

    def is_prime(self, n): # retourne True si n est un nombre premier
        for i in range(2,int(math.sqrt(n))+1):
            if (n%i) == 0:
                return False
        return True


    def get_hv(self, locaux):
        
        # return the number of graph in hor(n_h) and in vert(n_v) and a tuple with the list of positions for pyplot(plot:place) 
        nbre_locaux = len(locaux) # number of graphs to draw
        if nbre_locaux < 3:
            n_v = 2
            n_h = 1
            plot_place = (0,1,)
            return n_v, n_h, plot_place
        else:
            # if number of graph is a prime number increment it
            if self.is_prime(nbre_locaux): nbre_locaux += 1
            # get the square root of graph_nubmer
            sqr_nbre_locaux = math.sqrt(nbre_locaux)
            # get all the divisors for the graph_numer
            divisors = [i for i in range(2, nbre_locaux) if nbre_locaux % i == 0]
            # get the gap between divisors and square roor
            ecarts = {j : abs(d - sqr_nbre_locaux) for j, d in enumerate(divisors)} 
            # search the index of the smallest gap
            ecarts_values = list( ecarts.values())
            ecarts_keys = list( ecarts.keys())
            min_value = min( ecarts_values)
            divisor_index_min = ecarts_keys[ecarts_values.index(min_value)]
            # the divisor of the smalest gap is the hor number of graphs
            n_h = divisors[divisor_index_min]
            # calculate the vert number of graphs and if nbre vert is not and integer incrmente it
            n_v = int(nbre_locaux / n_h)
            if nbre_locaux / n_h != int(nbre_locaux / n_h): n_v += 1
            # get the presentation table for the graphs
            plot_place = () 
            plot_place += tuple((h,v) for h in range(n_h) for v in range(n_v))
        
        return n_v, n_h, plot_place

    def plot_air_data(self, locaux): #, l_names):
        
        n_v, n_h, plot_place = self.get_hv(locaux)
        fig, ax1 = plt.subplots(n_h, n_v)

        for i, local_d in enumerate (locaux.items()):
            
            local = local_d[0]
            label_val = local_d[1]
            print('Drawing', str(label_val))
            # get data from db
            time_x, ubat = self.get_bat_data(local)
            n_mes = len(ubat)
            #diff de bat
            data = {'time': time_x, 'bat': ubat}
            data_filtered = pd.DataFrame(data)
            filtered_bat = data_filtered['bat'].rolling(window=self.filter).mean()
            diff_bat = pd.Series.diff(filtered_bat)
            diff_bat = [b * 100 for b in diff_bat]  # convert values in %
            
            # calcul de la moyenne des n_moy dernières mesures
            n_moy = 4
            u_moy = 0
            u_moy += (sum(v for v in ubat[-n_moy:]))
            u_moy = round(u_moy / n_moy, 2)

            if len(ubat) != 0:
                # adjust the size of the graph to the screen
                screen_dpi = 90
                width, height = pyautogui.size()
                fig.set_figheight(height / screen_dpi)
                fig.set_figwidth(width / screen_dpi)

                #elapsed time
                elapsed, elaps_hm = self.get_elapsed_time(local)
                # battery voltage , filtered voltage and delta voltage in %
                ax1[plot_place[i]].tick_params(labelrotation=45)
                ax1[plot_place[i]].set_ylabel('Ubat [V]')
                ax1[plot_place[i]].set_title(label_val.lower())
                ax1[plot_place[i]].grid(True)
                ax1[plot_place[i]].plot(time_x, ubat, color='#a2653e', zorder=0)

                legend2 = ax1[plot_place[i]].legend(['Vie batterie: ' + elapsed
                            + ' (' + elaps_hm + ") (" + str(n_mes) + " mes) Umoy last " + str(n_moy) + " measures: "
                            + str(u_moy) + "V"], loc='upper left')

                # temporary not display the d(bat/dt) trace
                make_ax2 = False
                if make_ax2:
                    ax2_color = 'goldenrod'#'wheat' #'sienna'
                    ax2 = ax1[plot_place[i]].twinx()
                    ax2.tick_params(labelrotation=0)
                    ax2.set_ylabel('d(bat/dt) [%]', color=ax2_color, zorder=10)
                    ax2.plot(time_x, diff_bat, color=ax2_color)
                    ax2.tick_params(axis='y', labelcolor=ax2_color)
                    ax2.legend(['delta ubat filtered %'], loc='lower left')
#                     d_m = 0.2
#                     ax2.set_ylim(-d_m, d_m)


                #elapsed time
                elapsed = self.get_elapsed_time(local)
                # Combine all the operations and display
                fig.suptitle(label_val.upper() + ' [' + PROGRAM_NAME + ' version:' + VERSION_NO + ']')
#                 filter_hd = self.filter/self.intervalle
#                 filter_h = int(filter_hd)
#                 filter_m = int((filter_hd - filter_h) * 60)
                fig.suptitle(PROGRAM_NAME.upper() + ' (V' + VERSION_NO)
                plt.subplots_adjust(left=0.1,
                                    bottom=0.1,
                                    right=0.9,
                                    top=0.9,
                                    wspace=0.2,
                                    hspace=0.4)
                plt.xticks(rotation=30)
#                 ax1[plot_place[i]].set_yticks(
#                     np.linspace(ax1[plot_place[i]].get_yticks()[0], ax1[plot_place[i]].get_yticks()[-1], len(ax1[plot_place[i]].get_yticks())))
                ax1[plot_place[i]].set_yticks([3, 3.25, 3.5, 3.75, 4, 4.25, 4.5])
                if make_ax2:
#                     ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1[plot_place[i]].get_yticks())))
                    ax2.set_yticks([-0.1, -0.05, 0, 0.05, 0.1, 0.15, 0.2])
            else:
                print(label_val + ' ne contient aucune donnée')

        plt.show()  # plot

    def main(self):
        print('runing airsen_graph V' + VERSION_NO)
        locaux = {
            'mtl-2':'mtl2-2 hdc1080 1S1P Li-Ion 15min',
            'myst':'myst hdc1080 1S1P Li-Ion 15min',
            'solar':'solar hdc1080 1S1P Li-Ion 15min',
            'first_1':'first_1 hdc1080 1S1P Li-Ion 15min',
            }
        print('nbre_locaux:',len(locaux))
        self.plot_air_data(locaux)

if __name__ == '__main__':
    # instantiate the class
    airsens_bat_graph = AirSensBatGraph()
    # run main
    airsens_bat_graph.main()
