#!/bin/bash
echo " saving in /media/pi/rootfs/home/pi/filename.xxx"
echo "------------------------------------------------"
echo "saving database airsens ..."
sudo mysqldump -uroot -pmablonde airsens > /media/pi/rootfs/home/pi/airsens_db.sql
echo "saving database logger ..."
sudo mysqldump -uroot -pmablonde logger > /media/pi/rootfs/home/pi/logger_db.sql
echo "all db saved"
