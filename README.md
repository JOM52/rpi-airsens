# Projet : esp32-airsens 

Version 06_tld

***esp32-airsens*** est un projet de développement de capteurs ainsi que des application nécessaires pour les mettre en œuvre dans un environnement domotique. Le réseau sera constitué de capteurs qui transmettent les données à une centrale. Les capteur font l'objet d'un développement spécifique hardware et software autour du processeur ESP32 et à l'aide de Micropython et un système Liligo TTGO est utilisé tel quel pour la centrale . La centrale réceptionne les messages des capteurs, les transmet au broker MQTT, et se charge de l'affichage des mesures ainsi que de l'état de charge des batteries.

La version hard 06_tld est une version pour test longue durée avant la réalisation d'un circuit imprimé et d'un boitier dédicacé. (***06***: 6ème version du hard et ***tld*** pour **<u>t</u>**est **<u>l</u>**ongue **<u>d</u>**urée)

La version soft est 1.0.0 première version de production. 

**ci-après version améliorée par Chat GPT**

***esp32-airsens** est un projet qui vise à créer des capteurs intelligents et connectés pour la domotique. Ces capteurs utilisent le processeur ESP32 et le langage Micropython pour mesurer différents paramètres environnementaux et les envoyer à une centrale via un réseau sans fil. La centrale est basée sur un système Liligo TTGO qui reçoit les données des capteurs, les publie sur un broker MQTT et affiche les informations pertinentes sur un écran, notamment la température, le taux d’humidité, la pression atmosphérique et le niveau de charge de batterie des capteurs.*

*La version hard 06_tld est une version expérimentale qui permet de tester la fiabilité et la performance des capteurs sur une longue période avant de concevoir un circuit imprimé et un boitier adaptés.* 

*La version soft est 1.0.0 et correspond à la première version stable et fonctionnelle du logiciel.*

## Schéma de principe
https://github.com/JOM52/esp32-airsens-tld/blob/main/doc/Sch%C3%A9ma%20de%20principe.jpg

## Etat de développement de la version 06_tld

Cette version sera utilisée pour valider le schéma hardware, valider les calculs de la durée de vie des accus et tester les logiciels des capteurs et de la centrale.

## Elément capteur:

Afin de minimiser la consommation, cette version n'inclus pour le hardware que le strict minimum pour assurer le fonctionnement du capteur. La communication avec un PC pour la configuration est faite à l'aide d'une interface FTDI (USB to UART) connectée à la demande et les batteries sont rechargées hors du système. 

Dans l'exemple ci-après, le capteur est un BME 280 qui permet la mesure de la température, du taux d'humidité et de la pression atmosphérique.
https://github.com/JOM52/esp32-airsens-tld/blob/main/schema/Airsens%20v06_tld.jpg. 

Des capteurs de type hdc1080 ne permettant que la mesure de la température  et de l'humidité relative peuvent aussi être utilisés

### Hardware

Le hardware ESP32 est prévu pour pouvoir utiliser différents types de capteurs I2C. 

### Software

Chaque type de capteur a son propre driver. La structure globale du programme sera conservée pour optimiser la consommation.

Dans la version actuelle, il est prévu que chaque capteur transmette une nouvelle mesure chaque 5 minutes. Ainsi on peur espérer une durée de vie d'une batterie Li-Ion d'environ 2Ah (type 18650)  d'environ une année.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
file: airsens_now_sensor.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-airsens-now

The sensors are made with an ESP32 microcontroller and can be powered by battery or by USB.
They transmit the data to a central also realized with an ESP32 by a ESPnow interface

v0.1.0 : 17.08.2022 --> first prototype based on airsens_ble_sensor.py
----------------------------------------------------------------------
v0.2.0 : 07.09.2022 --> modified for new log_and_count.py version ---> no more compatible with previous versions
v0.2.1 : 07.09.2022 --> espnow and wifi powered off before going to deepsleep
v0.2.2 : 19.12.2022 --> small cosmetices changes
v0.2.3 : 20.12.2022 --> temporary change for develop proxy display
v0.2.4 : 03.01.2022 --> added fake sensor for test
v0.2.5 : 11.01.2023 --> name of the conf file modified to airsens_now_sensor_display_conf.py
v0.3.0 : 17.02.2023 --> new version for long time test (tld)
v0.3.1 : 26.02.2023 --> usage of conf values simplidied
----------------------------------------------------------------------
v1.0.0 : 12.03.2023 --> First production version - one version for bme280 and hdc1080
"""
from utime import ticks_ms, sleep_ms
start_time = ticks_ms()
# PARAMETERS ========================================
PRG_NAME = 'airsens_sensor.py'
PRG_VERSION = '1.0.0'
import airsens_sensor_conf as conf  # configuration file
from machine import Pin, freq, TouchPad
from machine import ADC, SoftI2C, deepsleep
from sys import exit
from lib.log_and_count import LogAndCount
log = LogAndCount()
if conf.SENSOR_TYPE == 'bme280':
    import lib.bme280 as bme280
elif conf.SENSOR_TYPE == 'hdc1080':
    import lib.hdc1080 as hdc1080
from network import WLAN, STA_IF
from espnow import  ESPNow

DIV = conf.R2 / (conf.R1 + conf.R2)  
pot = ADC(Pin(conf.ADC1_PIN))            
pot.atten(ADC.ATTN_6DB ) # Umax = 2V
pot.width(ADC.WIDTH_12BIT) # 0 ... 4095

def main():
    
    try:
        print('=================================================')
        print(PRG_NAME + ' - ' + PRG_VERSION)
        i = log.counters('passe', True)

        # instanciation of I2C
        i2c = SoftI2C(scl=Pin(conf.BME_SCL_PIN), sda=Pin(conf.BME_SDA_PIN), freq=10000)
        # instanciation of sensor
        if conf.SENSOR_TYPE == 'bme280':
            sensor = bme280.BME280(i2c=i2c)
        elif conf.SENSOR_TYPE == 'hdc1080':
            sensor = hdc1080.HDC1080(i2c=i2c)
        # init readings variables
        temp = 0
        hum = 0
        pres = 0
        air = 0
        bat = 0
        # read the values
        for l in range(conf.AVERAGING_BME):
            if conf.SENSOR_TYPE == 'hdc1080':
                temp += float(sensor.temperature())
                hum += float(sensor.humidity())
            elif conf.SENSOR_TYPE == 'bme280':
                pres += float(sensor.pressure)
                temp += float(sensor.temperature)
                hum += float(sensor.humidity)
        # read the battery voltage
        for l in range(conf.AVERAGING_BAT):
            bat += pot.read()
        # averaage the measurements
        temp = temp / conf.AVERAGING_BME
        hum = hum / conf.AVERAGING_BME
        pres = pres / conf.AVERAGING_BME
        bat = bat / conf.AVERAGING_BAT * (2 / 4095) / DIV
        # create the message
        msg = 'jmb,' + conf.SENSOR_LOCATION + ',' + str(temp) + ',' + str(hum) + ',' + str(pres) + ',' + str(bat)
        print('msg:', '"' + msg + '"')
        # A WLAN interface must be active to send()/recv()
        sta = WLAN(STA_IF)
        sta.active(True)
        # instantiation of ESPNow
        espnow = ESPNow()
        espnow.active(True)
        espnow.add_peer(conf.PROXY_MAC_ADRESS)
        # send the message
        espnow.send(msg)
        # close the communication canal
        espnow.active(False)
        espnow = None
        sta.active(False)
        sta = None
        # prepare for deepsleep
        total_time = ticks_ms() - start_time
        t_deepsleep = max(conf.T_DEEPSLEEP_MS - total_time, 10)
        # check the level of the battery
        if bat > (0.98 * conf.UBAT_0) or not conf.ON_BATTERY:
            # finishing tasks
            print('passe', i, '- error count:', log.counters('error', False),'-->' , str(total_time) + 'ms')
            print('going to deepsleep for: ' + str(t_deepsleep) + ' ms')
            print('=================================================')
            deepsleep(t_deepsleep)
        else:
            pass_to_wait = 10
            for i in range(pass_to_wait):
                print('going to endless deepsleep in ' + str(pass_to_wait - i) + ' s')
                sleep_ms(1000)
            print('Endless deepsleep due to low battery')
            deepsleep()
        
    except Exception as err:
        log.counters('error', True)
        log.log_error('airsens_sensor main error', log.error_detail(err))
        print('going to deepsleep for: ' + str(conf.T_DEEPSLEEP_MS) + ' ms')
        deepsleep(conf.T_DEEPSLEEP_MS)

if __name__ == "__main__":
    main()

```



### Messages
Les valeurs mesurées pour chaque grandeur sont regroupées et transmises au broker dans un seul message. Le format est le suivant:

`msg = (str(passe) + ',' + location + ',' + str(temp) + ',' + str(hum) + ',' + str(pres) + ',' + str(bat))`

Chaque valeur est convertie en string et les différents éléments sont séparés par des virgules. 

Dans cet exemple, les valeurs transmises sont: *no de la passe, location du capteur, température, humidité relative, pression atmosphérique et tension de la batterie*

#### *Messages, évolution possible*

*Le concept de message actuel complique la mise en œuvre de nouveaux capteurs qui pourraient mesurer des grandeurs différentes. Dans le but d'uniformiser l'usage de nouveau capteurs, il faudrait que chaque grandeur mesurée soit transmise dans un message spécifique mais d'un format unique (si un capteur peut mesurer plusieurs grandeurs alors plusieurs messages seraient transmis). Le message comprendrait la mesure d'une grandeur pour un capteur. Le message serait structuré comme suit:* 

1. ***IDENTIFIANT DU RESEAU DE MESURE:** un code permettant à la centrale de reconnaître le message comme lui étant adressé.*
2. ***TOPIC:** correspond à la **mac_adress** du capteur*
3. ***TYPE DE MESURE:*** 
   - *te --> temperature*
   - *hu --> humidité*
   - *pa --> pression atmosphérique*
   - *ub --> tension batterie*
   - *uc --> tension cellule photovoltaique*
   - *ic --> courant cellule photovoltaique*
   - *pc --> puissnce cellule photovoltaique*
   - *wc --> énergie fournie par les cellules*
   - *wt --> énergie totale consommée*
   - *...*
4. ***VALEUR**: transmise sous forme de string avec, si nécessaire, le point comme séparateur décimal et la résolution souhaitée*

*Chaque grandeur (température, humidité, pression, ...) est transmise dans son propre message, par exemple pour le capteur BME 280, pour une mesure, trois messages seront transmis avec les informations suivantes:*

***jmb** = IDENTIFIANT* , ***b'<a\x05\x0c\xe7('** = TOPIC (mac_adress du capteur)*, ***te** = TYPE DE MESURE*, ***23.5** = VALEUR*

*et cela produirait les messages suivants pour une seule mesure:*

1. *jmb,b'<a\x05\x0c\xe7(',te,23.5		température = 23.5C*
2. *jmb,b'<a\x05\x0c\xe7(',hu,65          humidité relative = 65%*
3. *jmb,b'<a\x05\x0c\xe7(',pa,980        pression atmosphérique = 980mBar*

*et éventuellement un message supplémentaire pour l'état de la batterie de ce capteur*

- *jmb,b'<a\x05\x0c\xe7(',ub,3.92       tension de la batterie 3.92V*

### Fichier de configuration

Pour permettre de paramétrer simplement un capteur, un fichier de configuration est lu à chaque boot. Ce fichier n'est pas structuré mais utilise simplement la syntaxe Micropython pour attribuer des valeurs à des variables. Cette procédure est économique en temps processeur. Ainsi les changements de paramètres se font simplement, dans un seul fichier facilement accessible et sans devoir parcourir et rechercher les constantes à adapter dans tout le code. L'indication des sections n'est pas indispensable mais est utile pour comprendre le rôle de chaque paramètre.

##### *version améiorée par Chat GPT*

*Afin de faciliter la configuration d'un capteur, un fichier de configuration est lu à chaque démarrage. Ce fichier n'a pas besoin d'une structure particulière, il utilise simplement la syntaxe Micropython pour assigner des valeurs à des variables. Cette procédure permet de réduire le temps de calcul du processeur. De cette façon, les modifications de paramètres se font facilement, dans un seul fichier accessible et sans avoir à chercher et modifier les constantes dans tout le code. L'indication des sections est facultative mais elle aide à comprendre le rôle de chaque paramètre.*

#### Sections:

- [ ] *acquisitions*: **SENSOR_ID** : identification du capteur et **T_DEEPSLEEP_MS** : temps de sommeil entre deux  mesures en ms
- [ ] *power supply*:  **UBAT_0** : Tension de batterie minimale. En dessous il faut déclencher le capteur 
- [ ] *I2C hardware config*: **BME_SDA_PIN** et **BME_SCL_pin** : pin pour le bus I2C
- [ ] *analog voltage measurement* : **R1** et **R2** : valeur des résistances du pont diviseur pour la mesure de la tension de batterie et **ADC1_PIN** : pin pour la mesure de U bat
- [ ] *averaging of measurements* : **AVERAGING_BAT** et **AVERAGING_BME** nombre de mesures à faire pour moyennage sur la batterie et sur le capteur à chaque acquisition  
- [ ] *ESP-NOW* : **PROXY_MAC_ADRESS** : adresse MAC de la centrale

#### Exemple:

```
#acquisitions
SENSOR_ID = 'tld_06d' 
T_DEEPSLEEP_MS = 10000

# power supply
ON_BATTERY = True
UBAT_100 = 4.2
UBAT_0 = 3.2

# I2C hardware config
BME_SDA_PIN = 21
BME_SCL_pin = 22

# analog voltage measurement
R1 = 977000 # first divider bridge resistor
R2 = 312000 # second divider bridge resistor
ADC1_PIN = 35 # Measure of analog voltage (ex: battery voltage following)

#averaging of measurements
AVERAGING_BAT = 5
AVERAGING_BME = 5

# ESP-now
PROXY_MAC_ADRESS = b'<a\x05\x0c\xe7('
```

### Principe du logiciel capteur

Pour économiser l'énergie consommée, le capteur est placé en ***deepsleep*** entre chaque mesure. Le temps de sommeil est défini dans le fichier de configuration en principe 5 minutes. Lors d'un éveil, le capteur lit le fichier de configuration, initialise les constantes, charge les librairies nécessaire, initialise le capteur, fait la mesure, mesure l'état de la batterie, transmets les valeurs à la centrale puis se met en ***deepsleep***

## Centrale

### Software

La centrale 

- reçoit et reconnait les messages valides, 
- configure les messages pour l'application de domotique choisie,
- transmet les valeurs de mesure à MQTT, 
- affiche différentes informations sur les mesures et l'état des batteries des capteurs. 

Les messages reçus ne sont pas confirmés au capteur. Ainsi des messages peuvent être perdus si la centrale n'est pas disponible au moment ou le capteur envoie un nouveau message. Cela me semble acceptable pour les mesures de grandeurs physiques qui évoluent relativement lentement dans le temps.

Dans l'état actuel, un capteur qui connaît la ***mac_adress*** de la centrale peut lui transmettre des mesures. Si la structure du message reçu est correcte, alors la centrale l'accepte. Si le capteur est déjà reconnu, les nouvelles valeurs remplacent les anciennes et si c'est un nouveau capteur, il est automatiquement reconnu et enregistré dans le fichier de configuration et dans la mémoire programme. 

La version actuelle utilise les deux boutons existants sur la version hard des Lilygo-ttgo pour sélectionner les différents affichages programmés. La sélection d'une option se fait lorsque l'utilisateur s'arrête suffisamment longtemps (2s) sur cette option.

Pour transmettre les mesures à MQTT, la centrale s'appuie sur le réseau WIFI. Les valeurs de mesure sont mises en forme selon les besoins de l'application de domotique choisie (domoticz, jeedom, ...) puis transmises au ***broker*** MQTT qui les publie à l'intension des abonnés.

##### *version améliorée par Chat GPT*

*La centrale est le cœur du système de domotique. Elle a plusieurs fonctions :*

- *Elle reçoit et traite les messages valides envoyés par les capteurs sans fil.*
- *Elle adapte les messages au format de l'application de domotique choisie (domoticz, jeedom, ...).*
- *Elle transmet les valeurs de mesure à MQTT, un protocole de communication qui permet de diffuser les informations aux abonnés.*
- *Elle affiche différentes informations sur un écran tactile, comme les mesures et l'état des batteries des capteurs.*

*Les messages reçus ne sont pas confirmés au capteur. Cela signifie que si la centrale n'est pas disponible au moment où le capteur envoie un nouveau message, celui-ci est perdu. Cela ne pose pas de problème pour les mesures de grandeurs physiques qui varient peu dans le temps.*

*La centrale accepte tous les messages qui ont une structure correcte et qui proviennent d'un capteur dont elle connaît l'adresse MAC. Si le capteur est déjà enregistré dans le fichier de configuration et dans la mémoire programme, les nouvelles valeurs remplacent les anciennes. Sinon, le capteur est automatiquement reconnu et ajouté au fichier de configuration et à la mémoire programme.*

*La centrale dispose de deux boutons sur la version matérielle des Lilygo-ttgo qui permettent de sélectionner les différents affichages programmés. La sélection d'une option se fait en restant appuyé sur le bouton pendant 2 secondes.*

*Pour transmettre les mesures à MQTT, la centrale se connecte au réseau WIFI. Les valeurs de mesure sont formatées selon les besoins de l'application de domotique choisie puis envoyées au broker MQTT qui les publie aux abonnés.*

### Fichier de configuration

Le fichier de configuration est un fichier standard Micropython. 

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: airsens_central_conf.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/JOM52/esp32-airsens-class

v0.4.0 : 05.02.2023 --> first prototype
"""
from ubinascii import hexlify
from machine import unique_id
# MQTT
BROKER_IP = '192.168.1.108'
TOPIC = 'airsens_now_test'
BROKER_CLIENT_ID = hexlify(unique_id())

# TTGO
BUTTON_MODE_PIN = 35
BUTTON_PAGE_PIN = 0
MODES = ['AUTO', 'OVERVIEW', 'BATTERY', 'DEADS', 'AGE']  # modes
DEFAULT_MODE = 2
DEFAULT_ROW_ON_SCREEN = 5
SILENT_TIME_TO_BE_DEAD = 3600 # seconds
CHOICE_TIMER_MS = 1000 # milli seconds
REFRESH_SCREEN_TIMER_MS = 15000 # milli seconds
BUTTON_DEBOUNCE_TIMER_MS = 10 # milli seconds

# WIFI
WIFI_WAN = 'jmb-home'
WIFI_PW = 'lu-mba01'

# BATTERY
BAT_OK = 3.4
BAT_LOW = 3.3
BAT_AGES_FILE = 'bat_ages.py'
```

- [ ] *MQTT* : 
  **BROKER_IP**: adresse IP du broker MQTT, 
  **TOPIC**: sujet du message, doit être connu par les abonnés, 
  **BROKER_CLIENT_ID**: ID unique de l'éditeur

- [ ] *TTGO*: 
  **BUTTON_MODE_PIN, BUTTON_PAGE_PIN**: no de pin sur lesquelles les boutons sont connectés

  **MODES**: différents modes d'affichage
  **DEFAULT_MODE**: mode de démarrage par défaut (voir ci-dessus)
  **DEFAULT_ROW_ON_SCREEN**: nombre de lignes possibles sur l'écran du TTGO
  **SILENT_TIME_TO_BE_DEAD**: nombre de secondes inactivité d'un capteur pour qu'il soit considéré comme mort
  **CHOICE_TIMER_MS**: nombre de ms sans action utilisateur pour qu'un choix soit validé
  **REFRESH_SCREEN_TIMER_MS**: nombre de ms en deux rafraichissements d'écran
  **BUTTON_DEBOUNCE_TIMER_MS**: nombre de ms nécessaires pour supprimer les rebonds des boutons

- [ ] WIFI:
  **WIFI_WAN**: SSID du WAN
  **WIFI_PW**: mot de passe du WAN
- [ ] BATTERY:
  **BAT_OK**: tension au dessus de laquelle la batterie est considérée comme suffisamment chargée
  **BAT_LOW**: tension au dessous de laquelle il faut informer l'utilisateur que la charge de la batterie est faible
  **BAT_AGE_FILE**: nom du fichier dans lequel l'âge des batteries est enregistré

#### *Evolutions*

*Dans une prochaine version il est prévu de modifier le programme pour:*

- *introduire un processus d'identification et d'enregistrement des capteurs par la centrale. Ainsi seuls des capteurs reconnus, validés et enregistrés seront autorisés à transmettre des mesures à la centrale.*
- *de crypter les message pour empêcher que les messages soient lus par des entités non autorisées.*

### Hardware

La centrale utilise un circuit Lilygo-ttgo qui comprend le processeur, une interface USB, un affichage de 135x240 pixels et deux boutons. Dans la version actuelle, ce circuit est utilisé tel quel. Les boutons sont utilisés comme suit:

- bouton 1 --> next **Mode**

- bouton 2 --> next **Page**

  le choix se fait lorsque aucun bouton n'est pressé pendant 1 secondes

#### *Evolutions*

*Dans une version future, il est prévu d'y adjoindre un joystick pour permettre à l'utilisateur une compréhension intuitive des manipulations.*

- *haut-bas pour choix **Page***

- *gauche-droite pour choix **Mode***

- *centre pour **ok***

  *le choix se fait par pression sur le bouton ok*

## MQTT mosquitto

Le logiciel MQTT fonctionne comme un éditeur (broker). Il est à l'écoute des auteur (publishers) qui publient des données et les diffuse auprès des abonnés (subscribers).

MQTT est installé comme un service sur un Raspberry PI. Il reçoit les informations depuis les auteurs qui publient les données (les capteurs) et les rediffuse vers tous les abonnés sans aucun contrôle de validité. Son rôle se limite à faire transiter les données depuis les auteurs vers les abonnés. 

Pour recevoir les données depuis le broker il suffit souscrire au broker sur le TOPIC concerné.

*description de l'installation et de la configuration de MQTT à placer ici* 

## Programme python airsens_mqtt

C'est un programme Python qui s'abonne à des topics MQTT pour les capteurs dont les données doivent être enregistrées dans une base de données. Ce programme est installé comme un service sur le raspberry PI. 

Il consulte le fichier de configuration de la centrale pour connaitre les mac-adress des capteurs reconnus par la centrale.

Il reçoit les données depuis MQTT, vérifie que le capteur est reconnu et, si oui, les enregistre dans la base de données airsens sur MariaDB (anciennement MySql) sur le Raspberry PI .

Ce programme se charge également d'alarmer l'utilisateur (par un mail, un WhatsApp ou autre) lorsque l'accumulateur d'un capteur doit être rechargé. 

*description de l'installation d'un service sur RPI à placer ici*

## Programme de domotique

Les mesures des capteurs peuvent, si nécessaire, être transmis à un logiciel de domotique (domoticz, jeedom, ...) pour être représentés graphiquement ou intervenir dans différentes alarmes. 

Ce thème fera objet d'un futur projet.

## GITHUB

Ce projet est maintenu dans GitHub, avec une licence GPL. Il est accessible par le lien 
https://github.com/JOM52/esp32-airsens-tld





Todi, Venise et Pravidondaz février-mars 2023







