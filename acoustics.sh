#!/bin/bash

sudo ./home/pi/hornet/fft/fft 1 1
rsync -azu -e ssh /home/pi/hornet/fft/10.csv odroid@192.168.1.20:/home/odroid/
sudo ./home/pi/hornet/fft/fft 1 2
rsync -azu -e ssh /home/pi/hornet/fft/20.csv odroid@192.168.1.20:/home/odroid/
sudo ./home/pi/hornet/fft/fft 1 3
rsync -azu -e ssh /home/pi/hornet/fft/30.csv odroid@192.168.1.20:/home/odroid/